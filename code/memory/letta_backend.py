"""LettaBackend: wraps letta_client.Letta talking to a local Letta server.

If no local server is reachable (default localhost:8283) and no LETTA_API_KEY
is provided, the backend marks itself unhealthy and the arm is logged as
SKIPPED at eval time. This is the documented degradation strategy from
architecture/v1.md.

To run a local server:
    pip install letta              # (separate venv if needed; otel conflicts in main)
    letta server start             # serves on 0.0.0.0:8283
or:
    docker run -d -p 8283:8283 letta/letta:latest

Scope mapping:
- We map our scope dict to a stable Letta `agent_id` via hash. One agent per
  scope. Memories are added as messages and surfaced via Letta's archival
  memory (which is what Letta exposes for long-term).
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, List, Optional

from adapters.schema import Turn
from .base import Memory, MemoryBackend


def _scope_hash(scope: Dict[str, Any]) -> str:
    keys = sorted(scope.keys())
    s = "|".join(f"{k}={scope[k]}" for k in keys)
    return hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()[:12]


class LettaBackend(MemoryBackend):
    backend_name = "letta"

    DEFAULT_BASE_URL = "http://localhost:8283"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config, scope)
        base_url = self.config.get("base_url", os.environ.get("LETTA_BASE_URL", self.DEFAULT_BASE_URL))
        api_key = self.config.get("api_key", os.environ.get("LETTA_API_KEY"))
        self._agent_id: Optional[str] = None
        self._client = None
        try:
            from letta_client import Letta  # type: ignore

            client_kwargs: Dict[str, Any] = {}
            if api_key:
                client_kwargs["api_key"] = api_key
            else:
                # Local server: pass placeholder; client requires api_key arg
                client_kwargs["api_key"] = "local-no-auth"
            client_kwargs["base_url"] = base_url
            self._client = Letta(**client_kwargs)
            # Probe with a cheap call: list agents
            agents = self._client.agents.list(limit=1)
            self._health.healthy = True
            self._health.embedding_model = "letta-default"
            self._health.extra["base_url"] = base_url
            self._health.extra["api_key_present"] = bool(api_key)
            self._health.extra["probe"] = "ok"
            self._health.extra["agents_probe_count"] = len(list(agents)) if agents else 0
        except Exception as e:
            self._health.healthy = False
            self._health.error_message = (
                f"Letta server unreachable at {base_url}: {type(e).__name__}: {str(e)[:200]}"
            )

    # G4 Loop 4: discover the model handle from the live Letta server at init time
    # so the hardcoded "openai/gpt-4o-mini" 404 problem can never recur. Cache
    # the discovered handles on first lookup.
    def _discover_model_handles(self) -> Dict[str, Optional[str]]:
        """Query the Letta server for available LLM and embedding handles.

        Returns {"llm": <handle>, "embedding": <handle>} where each value is
        the first available handle of that model type, or None if none found.
        Uses HTTP fallback so we don't depend on whichever client SDK shape
        ships today.
        """
        cached = getattr(self, "_model_handles_cached", None)
        if cached is not None:
            return cached
        result: Dict[str, Optional[str]] = {"llm": None, "embedding": None}
        try:
            import urllib.request
            import json as _json
            base = self._health.extra.get("base_url") or self.DEFAULT_BASE_URL
            # 1) LLMs are listed at /v1/models/
            with urllib.request.urlopen(
                base.rstrip("/") + "/v1/models/", timeout=5
            ) as resp:
                llm_list = _json.loads(resp.read().decode("utf-8")) or []
            for m in llm_list:
                if m.get("model_type") == "llm" and m.get("handle"):
                    result["llm"] = m["handle"]
                    break
            # 2) Embeddings are listed at /v1/models/embedding
            with urllib.request.urlopen(
                base.rstrip("/") + "/v1/models/embedding", timeout=5
            ) as resp:
                emb_list = _json.loads(resp.read().decode("utf-8")) or []
            for m in emb_list:
                if m.get("model_type") == "embedding" and m.get("handle"):
                    result["embedding"] = m["handle"]
                    break
        except Exception as e:
            self._health.extra["discover_models_error"] = str(e)[:200]
        self._model_handles_cached = result
        return result

    def _ensure_agent(self, scope: Dict[str, Any]) -> Optional[str]:
        if not self._client or not self._health.healthy:
            return None
        if self._agent_id:
            return self._agent_id
        name = f"phd-{_scope_hash(scope)}"
        try:
            # Try to find existing
            existing = self._client.agents.list(name=name, limit=1)
            existing_list = list(existing) if existing else []
            if existing_list:
                self._agent_id = existing_list[0].id  # type: ignore[attr-defined]
                # G4 Loop 4: record the resolved handles even when re-using
                # an existing agent. We pull them from the returned agent
                # object best-effort; if absent, surface "(existing)" so
                # the diagnostic at least confirms we found one.
                ex = existing_list[0]
                self._health.extra["agent_model"] = (
                    getattr(ex, "model", None)
                    or getattr(getattr(ex, "llm_config", None), "handle", None)
                    or "(existing-agent-unknown)"
                )
                self._health.extra["agent_embedding"] = (
                    getattr(ex, "embedding", None)
                    or getattr(getattr(ex, "embedding_config", None), "handle", None)
                    or "(existing-agent-unknown)"
                )
                return self._agent_id
            # G4 Loop 4: ask the live server which handles exist (replacing the
            # hardcoded "openai/gpt-4o-mini" + "openai/text-embedding-3-small"
            # that 404'd on the local server in Loop 3).
            handles = self._discover_model_handles()
            llm_handle = (
                self.config.get("model")
                or os.environ.get("ROOMD_LETTA_MODEL")
                or handles.get("llm")
                # Last-ditch fallback (will likely 404 but at least surfaces a real error)
                or "letta/letta-free"
            )
            emb_handle = (
                self.config.get("embedding")
                or os.environ.get("ROOMD_LETTA_EMBEDDING")
                or handles.get("embedding")
                or "letta/letta-free"
            )
            self._health.extra["agent_model"] = llm_handle
            self._health.extra["agent_embedding"] = emb_handle
            # Create new minimal agent
            agent = self._client.agents.create(
                name=name,
                description=f"PhD-eval scope {scope}",
                model=llm_handle,
                embedding=emb_handle,
            )
            self._agent_id = agent.id
            return self._agent_id
        except Exception as e:
            # G4 HONEST-Mem fix: use the central _record_error path so:
            #   - n_errors increments
            #   - last_error is set
            #   - healthy flips to False
            # The Loop 3 audit caught the original violation: error_message
            # was being set directly on _health, never via _record_error, so
            # n_errors, last_error, healthy stayed wrong.
            self._record_error(
                "letta.ensure_agent",
                f"{type(e).__name__}: {str(e)[:200]}",
            )
            return None

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        t0 = time.time()
        if not self._client or not self._health.healthy:
            self._record_op("add", error=True)
            return []
        merged = self.merged_scope(self.scope, scope)
        aid = self._ensure_agent(merged)
        if not aid:
            self._record_op("add", error=True)
            return []
        text = self.extract_substantive_text(turns, max_chars=2000)
        if not text.strip():
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            return []
        substantive = len(text) >= 100
        try:
            # Use archival memory insert (the long-term memory in Letta)
            res = self._client.agents.passages.create(
                agent_id=aid,
                text=text,
            )
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            ids: List[str] = []
            if isinstance(res, list):
                for p in res:
                    pid = getattr(p, "id", None)
                    if pid:
                        ids.append(pid)
            elif hasattr(res, "id"):
                ids.append(res.id)
            # HONEST-Mem: substantive input but zero ids returned == silent failure
            if substantive and not ids:
                self._record_error(
                    "letta.add",
                    "Letta passages.create returned no ids on substantive input",
                    silent_extraction=True,
                )
                return []
            # Update count to a real number (best-effort)
            try:
                self._health.n_memories = len(list(self._client.agents.passages.list(agent_id=aid, limit=10000) or []))
            except Exception:
                # Don't surface sentinel; leave previous count if unknown
                pass
            return ids
        except Exception as e:
            self._record_op("add", latency_ms=(time.time() - t0) * 1000, error=True)
            self._record_error("letta.add", f"{type(e).__name__}: {e}")
            return []

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        t0 = time.time()
        if not self._client or not self._health.healthy:
            self._record_op("search", error=True)
            return []
        merged = self.merged_scope(self.scope, scope)
        aid = self._ensure_agent(merged)
        if not aid:
            self._record_op("search", error=True)
            return []
        try:
            res = self._client.agents.passages.search(
                agent_id=aid,
                query=query,
                limit=k,
            )
            self._record_op("search", latency_ms=(time.time() - t0) * 1000)
            out: List[Memory] = []
            items = list(res) if res else []
            for p in items[:k]:
                out.append(
                    Memory(
                        memory_id=getattr(p, "id", ""),
                        text=getattr(p, "text", "") or "",
                        score=float(getattr(p, "score", 0.0) or 0.0),
                        scope=merged,
                        state="active",
                        metadata={"backend": self.backend_name},
                    )
                )
            return out
        except Exception as e:
            self._record_op("search", latency_ms=(time.time() - t0) * 1000, error=True)
            self._record_error("letta.search", f"{type(e).__name__}: {e}")
            return []

    def clear(self) -> None:
        if not self._client or not self._health.healthy or not self._agent_id:
            return
        try:
            self._client.agents.delete(agent_id=self._agent_id)
            self._agent_id = None
        except Exception:
            pass
