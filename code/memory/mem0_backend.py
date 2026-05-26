"""Mem0Backend: wraps mem0ai 2.0.x.

Configuration (pre-registered in architecture/v1.md §4.2):
- vector_store: qdrant on disk under <store_dir>/qdrant
- embedder:     fastembed (BAAI/bge-small-en-v1.5, 384-d)
- llm:          Anthropic Haiku for fact extraction (claude-3-5-haiku-latest)
                billed against subscription via ANTHROPIC_API_KEY if set; otherwise
                we set a placeholder and only the embedding path actually runs
                during smoke tests.

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

    DEFAULT_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
    DEFAULT_EMBEDDING_DIMS = 384
    DEFAULT_LLM_MODEL = "claude-3-5-haiku-latest"

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
        llm_model = self.config.get("llm_model", self.DEFAULT_LLM_MODEL)
        on_disk = bool(self.config.get("on_disk", True))

        # Ensure mem0 doesn't blow up on missing API key during smoke (won't extract)
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
                "provider": "anthropic",
                "config": {"model": llm_model},
            },
        }

        try:
            from mem0 import Memory as Mem0Memory  # type: ignore

            self._m = Mem0Memory.from_config(self._cfg)
            self._health.healthy = True
            self._health.embedding_model = embedding_model
            self._health.extra["collection"] = collection
            self._health.extra["store_dir"] = str(store_dir)
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
        try:
            result = self._m.add(messages=messages, user_id=uid)
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            # mem0 returns {"results": [{"id": ..., "memory": ..., "event": "ADD"|"UPDATE"|"NONE"}]}
            ids: List[str] = []
            for r in (result or {}).get("results", []) if isinstance(result, dict) else (result or []):
                mid = r.get("id") if isinstance(r, dict) else None
                if mid:
                    ids.append(str(mid))
            self._health.n_memories = self._count_memories(uid)
            return ids
        except Exception as e:
            self._record_op("add", latency_ms=(time.time() - t0) * 1000, error=True)
            self._health.error_message = (
                f"mem0 add failed: {type(e).__name__}: {str(e)[:200]}"
            )
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
            for it in items:
                if not isinstance(it, dict):
                    continue
                out.append(
                    Memory(
                        memory_id=str(it.get("id", "")),
                        text=str(it.get("memory", "")),
                        score=float(it.get("score", 0.0)),
                        scope=self.merged_scope(self.scope, scope),
                        state="active",
                        metadata={"backend": self.backend_name, "raw": it},
                    )
                )
            return out
        except Exception as e:
            self._record_op("search", latency_ms=(time.time() - t0) * 1000, error=True)
            self._health.error_message = (
                f"mem0 search failed: {type(e).__name__}: {str(e)[:200]}"
            )
            return []

    def _count_memories(self, user_id: str) -> int:
        try:
            res = self._m.get_all(user_id=user_id)  # type: ignore[union-attr]
            if isinstance(res, dict):
                return len(res.get("results", []))
            return len(res or [])
        except Exception:
            return -1

    def clear(self) -> None:
        if not self._m or not self._health.healthy:
            return
        uid = _scope_to_user_id(self.scope)
        try:
            self._m.delete_all(user_id=uid)
            self._health.n_memories = 0
        except Exception:
            pass
