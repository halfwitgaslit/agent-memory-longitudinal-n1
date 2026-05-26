"""Mem0Backend: wraps mem0ai 2.0.x.

Configuration (pre-registered in architecture/v1.md §4.2):
- vector_store: qdrant on disk under <store_dir>/qdrant
- embedder:     fastembed (BAAI/bge-small-en-v1.5, 384-d)
- llm:          Anthropic Haiku for fact extraction (claude-3-5-haiku-latest)
                routed through `claude -p` subscription billing if no real
                ANTHROPIC_API_KEY is present (see memory/claude_cli_llm.py).

KNOWN ISSUE (discovered Loop 2 D7, refined Loop 3 Investigator C): Mem0
opens a SHARED global qdrant at ~/.mem0/migrations_qdrant which is
exclusive-locked. Only ONE Mem0Backend instance can be alive per process
at a time AND the lock is not reliably released within the same process
even after explicit teardown. Specifically, Loop 3 verified that calling
client.close() followed by gc.collect() and time.sleep(1.0) is NOT
sufficient: constructing a new Mem0Backend in the same process
immediately fails with "Storage folder ~/.mem0/migrations_qdrant is
already accessed by another instance".

The only reliable workaround is SUBPROCESS ISOLATION — each Mem0Backend
open/close cycle must happen in its own subprocess so OS-level file
locks are released on process exit. In-process teardown does not work.
  - PREFERRED: spawn a subprocess for each open/close cycle
  - AVOID: relying on close() + gc + sleep to free the lock (does not work)
  - LAST RESORT: wipe ~/.mem0/migrations_qdrant between instances (race-prone)

This is a constraint of the mem0ai library, not our code. Phase 2 eval
loop will keep one long-lived Mem0Backend instance per arm; anything that
needs to cycle backends (e.g. per-arm setup/teardown across multiple
configs) must use subprocess isolation.

Mem0 v2 surface:
- m.add(messages, user_id, ...) → list of {id, memory, event, ...}
- m.search(query, user_id, limit) → list of {memory, score, ...}
- m.get_all(user_id) → list
- m.delete_all(user_id) → wipe

Scope mapping:
- We map our `scope` dict to mem0's `user_id` by hashing the scope into a
  stable key. Reserved keys (project, worktree, branch, cli) are concatenated.
"""

from __future__ import annotations

import hashlib
import os
import time
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.schema import Turn
from .base import Memory, MemoryBackend

# Suppress mem0's noisy pydantic serializer warnings during normal use
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def _scope_to_user_id(scope: Dict[str, Any], prefix: str = "phd_") -> str:
    """Hash a scope dict to a stable Mem0 user_id."""
    keys_in_order = ("user_id", "project", "worktree", "branch", "cli")
    parts: List[str] = []
    for k in keys_in_order:
        v = scope.get(k)
        if v is not None:
            parts.append(f"{k}={v}")
    if not parts:
        # Fall back to the whole scope dict
        parts = [f"{k}={scope[k]}" for k in sorted(scope.keys())]
    s = "|".join(parts)
    h = hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()[:16]
    return f"{prefix}{h}"


class Mem0Backend(MemoryBackend):
    backend_name = "mem0"

    def inspect(self) -> Dict[str, Any]:
        """Refresh n_memories from the live store before reporting."""
        if self._m and self._health.healthy:
            try:
                uid = _scope_to_user_id(self.scope)
                live = self._safe_count_memories(uid)
                if live >= 0:
                    self._health.n_memories = live
            except Exception:
                # Don't crash inspect on count refresh failure;
                # base.inspect() will raise if n_memories has been left as -1.
                pass
        return super().inspect()

    DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    DEFAULT_EMBEDDING_DIMS = 384
    DEFAULT_LLM_MODEL = "claude-3-5-haiku-latest"
    # When no real ANTHROPIC_API_KEY is present we route Mem0's internal LLM
    # calls through `claude -p` (the subscription-billed harness). The model
    # name there is the CLI's model name, not the API model.
    DEFAULT_CLI_LLM_MODEL = "claude-haiku-4-5"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config, scope)
        store_dir = Path(self.config.get("store_dir", "/tmp/phd_mem0_qdrant"))
        store_dir.mkdir(parents=True, exist_ok=True)
        collection = self.config.get(
            "collection",
            f"phd_{_scope_to_user_id(self.scope, prefix='')}",
        )
        embedding_model = self.config.get("embedding_model", self.DEFAULT_EMBEDDING_MODEL)
        embedding_dims = self.config.get("embedding_dims", self.DEFAULT_EMBEDDING_DIMS)
        on_disk = bool(self.config.get("on_disk", True))

        # Decide LLM routing:
        #   - explicit config llm_provider="claude_cli"  → always use claude_cli
        #   - explicit config llm_provider="anthropic" + ANTHROPIC_API_KEY → use API
        #   - no real API key (or key is "placeholder*") → use claude_cli (subscription)
        explicit_provider = self.config.get("llm_provider")
        api_key = os.environ.get("ANTHROPIC_API_KEY") or ""
        api_key_real = api_key and not api_key.lower().startswith("placeholder")

        if explicit_provider == "anthropic" or (api_key_real and explicit_provider != "claude_cli"):
            llm_provider = "anthropic"
            llm_model = self.config.get("llm_model", self.DEFAULT_LLM_MODEL)
            llm_cfg = {"model": llm_model}
        else:
            # Route through claude -p (subscription)
            llm_provider = "claude_cli"
            llm_model = self.config.get("llm_model", self.DEFAULT_CLI_LLM_MODEL)
            llm_cfg = {"model": llm_model}
            # Register the provider lazily (idempotent)
            from .claude_cli_llm import register_claude_cli_provider
            try:
                register_claude_cli_provider()
            except Exception as reg_e:
                # Fall back to anthropic provider with placeholder; the silent-failure
                # detection will fire and mark this unhealthy.
                self._health.extra["claude_cli_registration_error"] = str(reg_e)[:200]
                llm_provider = "anthropic"
                llm_cfg = {"model": self.DEFAULT_LLM_MODEL}
                os.environ.setdefault("ANTHROPIC_API_KEY", "placeholder-for-smoke")

        self._cfg = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": collection,
                    "embedding_model_dims": embedding_dims,
                    "path": str(store_dir),
                    "on_disk": on_disk,
                },
            },
            "embedder": {
                "provider": "fastembed",
                "config": {"model": embedding_model},
            },
            "llm": {
                "provider": llm_provider,
                "config": llm_cfg,
            },
        }

        try:
            from mem0 import Memory as Mem0Memory  # type: ignore

            self._m = Mem0Memory.from_config(self._cfg)
            self._health.healthy = True
            self._health.embedding_model = embedding_model
            self._health.extra["collection"] = collection
            self._health.extra["store_dir"] = str(store_dir)
            self._health.extra["llm_provider"] = llm_provider
            self._health.extra["llm_model"] = llm_model
        except Exception as e:
            self._health.healthy = False
            self._health.error_message = f"mem0 init failed: {type(e).__name__}: {e}"
            self._m = None

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        t0 = time.time()
        if not self._m or not self._health.healthy:
            self._record_op("add", error=True)
            return []
        # mem0 expects "messages" in {role, content} form. Map Turns → mem0 messages.
        messages: List[Dict[str, str]] = []
        for t in turns:
            text = ""
            for cb in t.content:
                if cb.kind == "text" and cb.text:
                    text += cb.text + "\n"
                elif cb.kind == "tool_use" and cb.name:
                    text += f"[used tool: {cb.name}]\n"
                elif cb.kind == "tool_result" and cb.output:
                    text += f"[tool_result snippet: {cb.output[:200]}]\n"
            if text.strip():
                role = "user" if t.role == "user" else "assistant"
                messages.append({"role": role, "content": text[:5000]})
        if not messages:
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            return []
        uid = _scope_to_user_id(self.merged_scope(self.scope, scope))
        # G10 Loop 4: tag every ingest with originating CLI so the eval
        # harness can attribute retrieved memories to their source CLI
        # later — critical in bridge mode where the user_id partition is
        # shared. The Turn schema (adapters/schema.py) already requires a
        # `cli` field of {"claude_code","codex"}. Take the modal CLI of
        # the input turns; if mixed, prefer the first non-None value.
        origin_cli = None
        for t in turns:
            tc = getattr(t, "cli", None)
            if tc:
                origin_cli = tc
                break
        # Effective scope for metadata stamping (so retrieval-time consumers
        # can inspect what was set at ingest time).
        effective_scope = self.merged_scope(self.scope, scope)
        metadata_for_mem0 = {
            "_origin_cli": origin_cli or "unknown",
            "_origin_scope_user_id": effective_scope.get("user_id"),
            "_origin_scope_project": effective_scope.get("project"),
            "_origin_scope_worktree": effective_scope.get("worktree"),
            "_origin_scope_branch": effective_scope.get("branch"),
            "_origin_scope_cli_at_ingest": effective_scope.get("cli"),
            "_phd_loop4_ingest_ts_utc": time.time(),
        }
        # Determine whether the input had substantive content (so a zero-id
        # return means silent extraction failure, not just trivial input).
        total_input_chars = sum(len(m["content"]) for m in messages)
        substantive = total_input_chars >= 100  # heuristic: ≥100 chars
        try:
            # Capture mem0's logger output to detect silent LLM failures
            # (mem0/memory/main.py:747 logs "LLM extraction failed: ..." at
            # error level but returns successfully with empty results).
            import logging
            import io

            mem0_logger = logging.getLogger("mem0")
            buf = io.StringIO()
            handler = logging.StreamHandler(buf)
            handler.setLevel(logging.ERROR)
            mem0_logger.addHandler(handler)
            prior_level = mem0_logger.level
            mem0_logger.setLevel(logging.ERROR)
            try:
                result = self._m.add(messages=messages, user_id=uid, metadata=metadata_for_mem0)
            finally:
                mem0_logger.removeHandler(handler)
                mem0_logger.setLevel(prior_level)
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            captured = buf.getvalue()
            # mem0 returns {"results": [{"id": ..., "memory": ..., "event": "ADD"|"UPDATE"|"NONE"}]}
            ids: List[str] = []
            for r in (result or {}).get("results", []) if isinstance(result, dict) else (result or []):
                mid = r.get("id") if isinstance(r, dict) else None
                if mid:
                    ids.append(str(mid))
            # Detect silent failure: substantive input but no ids extracted.
            # Two flavors:
            #   (a) mem0 logged an LLM extraction error (placeholder API key etc.)
            #   (b) no error logged, but mem0 returned zero results on substantive
            #       input — also suspicious. We treat (b) as a soft warning
            #       (warn-level last_error, don't flip unhealthy) because mem0
            #       legitimately returns zero when nothing extractable is found.
            silent_fail_signals = (
                "LLM extraction failed" in captured
                or "Could not resolve authentication" in captured
                or "Error parsing extraction response" in captured
                or "Expecting value" in captured
            )
            if not ids and substantive and silent_fail_signals:
                self._record_error(
                    "mem0.add",
                    f"silent LLM extraction failure (mem0 swallowed error). "
                    f"captured: {captured[:300]}",
                    silent_extraction=True,
                )
                # Don't update n_memories on failure
                return []
            if not ids and substantive and not silent_fail_signals:
                # Soft signal: record in extras so eval can sum them up
                self._health.extra["last_zero_extract_on_substantive_ts"] = time.time()
                self._health.extra["n_zero_extract_on_substantive"] = (
                    self._health.extra.get("n_zero_extract_on_substantive", 0) + 1
                )
            # Real count, fallback to existing count if get_all fails
            count = self._safe_count_memories(uid)
            if count >= 0:
                self._health.n_memories = count
            return ids
        except Exception as e:
            self._record_op("add", latency_ms=(time.time() - t0) * 1000, error=True)
            self._record_error("mem0.add", f"{type(e).__name__}: {e}")
            return []

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        t0 = time.time()
        if not self._m or not self._health.healthy:
            self._record_op("search", error=True)
            return []
        uid = _scope_to_user_id(self.merged_scope(self.scope, scope))
        try:
            # mem0 v2.0+ moved user_id into the filters dict for search()
            try:
                res = self._m.search(query=query, filters={"user_id": uid}, limit=k)
            except TypeError:
                # Some mem0 builds accept user_id directly
                res = self._m.search(query=query, user_id=uid, limit=k)
            self._record_op("search", latency_ms=(time.time() - t0) * 1000)
            out: List[Memory] = []
            items = (res or {}).get("results", []) if isinstance(res, dict) else (res or [])
            seen_ids: set = set()
            for it in items:
                if not isinstance(it, dict):
                    continue
                mid = str(it.get("id", ""))
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)
                # G10 Loop 4: surface CLI attribution + ingest scope. Mem0
                # stores per-add metadata in the `metadata` key on each
                # returned record; we lift our `_origin_cli` and friends up
                # to the Memory.metadata dict so callers don't have to dig
                # through `raw`.
                raw_meta = (it.get("metadata") if isinstance(it, dict) else None) or {}
                surfaced_meta: Dict[str, Any] = {
                    "backend": self.backend_name,
                    "raw": it,
                }
                for k_meta in (
                    "_origin_cli",
                    "_origin_scope_user_id",
                    "_origin_scope_project",
                    "_origin_scope_worktree",
                    "_origin_scope_branch",
                    "_origin_scope_cli_at_ingest",
                    "_phd_loop4_ingest_ts_utc",
                ):
                    if k_meta in raw_meta:
                        surfaced_meta[k_meta] = raw_meta[k_meta]
                out.append(
                    Memory(
                        memory_id=mid,
                        text=str(it.get("memory", "")),
                        score=float(it.get("score", 0.0)),
                        scope=self.merged_scope(self.scope, scope),
                        state="active",
                        metadata=surfaced_meta,
                    )
                )
            # Mem0's hybrid search (vector + BM25) can return more than `k`
            # raw items; enforce our contract by sorting on score and trimming.
            out.sort(key=lambda m: m.score, reverse=True)
            return out[:k]
        except Exception as e:
            self._record_op("search", latency_ms=(time.time() - t0) * 1000, error=True)
            self._record_error("mem0.search", f"{type(e).__name__}: {e}")
            return []

    def _safe_count_memories(self, user_id: str) -> int:
        """Return a real non-negative count.

        Post-Loop-4 G9 contract: NEVER returns a negative sentinel. If the
        underlying mem0 get_all() raises, we set self._health.last_error and
        return 0. Callers MUST inspect `last_error` if they need to
        distinguish "store is empty" from "count is unknown."

        mem0 v2 moved scope params into a `filters` dict for get_all().
        Try the v2 form first, fall back to the legacy form.
        """
        if not self._m:
            # Not initialized -> unknown count; report 0 with diagnostic
            self._health.last_error = "_safe_count_memories: backend not initialized"
            self._health.last_error_ts_utc = time.time()
            return 0
        try:
            # v2+ form
            res = self._m.get_all(filters={"user_id": user_id})  # type: ignore[union-attr]
        except TypeError:
            try:
                res = self._m.get_all(user_id=user_id)  # type: ignore[union-attr]
            except Exception as e:
                self._health.last_error = f"_safe_count_memories(legacy): {type(e).__name__}: {e}"
                self._health.last_error_ts_utc = time.time()
                return 0
        except Exception as e:
            # If v2-form raises for another reason, try the legacy as well
            try:
                res = self._m.get_all(user_id=user_id)  # type: ignore[union-attr]
            except Exception as e2:
                self._health.last_error = (
                    f"_safe_count_memories: v2={type(e).__name__}:{e}; "
                    f"legacy={type(e2).__name__}:{e2}"
                )
                self._health.last_error_ts_utc = time.time()
                return 0
        if isinstance(res, dict):
            return len(res.get("results", []))
        return len(res or [])

    # Keep old name as alias for any external callers (e.g., tests)
    def _count_memories(self, user_id: str) -> int:
        return self._safe_count_memories(user_id)

    def clear(self) -> None:
        if not self._m or not self._health.healthy:
            return
        uid = _scope_to_user_id(self.scope)
        try:
            self._m.delete_all(user_id=uid)
            self._health.n_memories = 0
        except Exception:
            pass
