"""HindsightBackend: wraps hindsight-api 0.6.x MemoryEngine (Loop 4 G5 rewrite).

Hindsight 0.6.x is async-first. The Loop 3 implementation used method
names like `record_observation` and `list_banks(context=...)` that do not
exist in the 0.6.x surface — every call no-op'd, the synthetic SHA1 ID
mimicked a successful add(), and recall() always returned empty.

The corrected surface used here (verified 2026-05-26 against
`hindsight_api 0.6.2`):

  - Banks: `get_bank_profile(bank_id, request_context=..., create_if_missing=True)`
    is the implicit-create entry-point. There is no public `create_bank`.
  - Ingest: `engine.retain(bank_id, content, context="", request_context=...)`
    is a SYNC wrapper around `retain_async`. Returns a list of memory_unit_ids.
  - Recall: `engine.recall(bank_id, query, fact_type, ...)` is sync.

Configuration:
- `db_url`: defaults to pg0-embedded local Postgres
- `embeddings`: LocalSTEmbeddings (sentence-transformers, no API key needed)
- `llm`: Anthropic Haiku for memory/retain/reflect/consolidation LLM calls;
  with `skip_llm_verification=True` we avoid hitting the API during init.
  Note: actual `retain` calls DO invoke the configured LLM unless the
  bank is configured for fact_type="world" with skip-LLM (per architecture
  spec we still run real LLM extraction in Phase 2). For smoke we
  accept the LLM might fail; HONEST-Mem surfaces that.

HONEST-Mem invariants enforced (G5 + G4 pattern):
- Any add()/search() exception flows through `_record_error` (increments
  n_errors, sets last_error, flips healthy=False).
- The synthetic SHA1 ID hack from Loop 2/3 is GONE. We return real
  memory_unit_ids from `retain` only when retain actually succeeded.
"""
from __future__ import annotations

import hashlib
import os
import time
from typing import Any, Dict, List, Optional

from adapters.schema import Turn

from .base import Memory, MemoryBackend


def _scope_namespace(scope: Dict[str, Any]) -> str:
    keys = sorted(scope.keys())
    s = "|".join(f"{k}={scope[k]}" for k in keys)
    h = hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()[:10]
    return f"phd_{h}"


class HindsightBackend(MemoryBackend):
    backend_name = "hindsight"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config, scope)
        self._engine = None
        self._bank_id: Optional[str] = None
        self._namespace = _scope_namespace(self.scope)
        # G5 Loop 4: keep a single persistent event loop alive for the
        # lifetime of this backend so SQLAlchemy/asyncpg pools stay bound
        # to one loop. Without this, asyncio.run() per call destroys the
        # loop and any DB pool tied to it, producing "Event loop is closed"
        # on the next call. We never call self._loop.close() inside the
        # backend lifecycle except in __del__.
        import asyncio
        self._loop = asyncio.new_event_loop()

        try:
            from hindsight_api import (  # type: ignore
                LocalSTEmbeddings,
                MemoryEngine,
            )

            db_url = self.config.get("db_url") or os.environ.get("HINDSIGHT_DB_URL")
            if not db_url:
                # Start the embedded pg0 (ships in dep tree). It's async.
                try:
                    from hindsight_api.pg0 import start_embedded_postgres  # type: ignore

                    db_url = self._loop.run_until_complete(start_embedded_postgres())
                except Exception as pg_e:
                    db_url = None
                    self._health.extra["pg0_error"] = str(pg_e)[:200]

            # Embeddings: local sentence-transformers (no cloud)
            embeddings = LocalSTEmbeddings(model_name=self.config.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            ))

            llm_provider = self.config.get("llm_provider", "anthropic")
            llm_model = self.config.get("llm_model", "claude-3-5-haiku-latest")
            # Hindsight checks any of these env vars for the LLM API key
            llm_api_key = (
                self.config.get("llm_api_key")
                or os.environ.get("HINDSIGHT_API_LLM_API_KEY")
                or os.environ.get("ANTHROPIC_API_KEY")
                or "placeholder-no-llm-during-smoke"
            )
            os.environ.setdefault("HINDSIGHT_API_LLM_API_KEY", llm_api_key)

            self._engine = MemoryEngine(
                db_url=db_url,
                embeddings=embeddings,
                memory_llm_provider=llm_provider,
                memory_llm_model=llm_model,
                memory_llm_api_key=llm_api_key,
                retain_llm_provider=llm_provider,
                retain_llm_model=llm_model,
                retain_llm_api_key=llm_api_key,
                reflect_llm_provider=llm_provider,
                reflect_llm_model=llm_model,
                reflect_llm_api_key=llm_api_key,
                consolidation_llm_provider=llm_provider,
                consolidation_llm_model=llm_model,
                consolidation_llm_api_key=llm_api_key,
                run_migrations=True,
                skip_llm_verification=True,
                lazy_reranker=True,
            )

            self._health.healthy = True
            self._health.embedding_model = self.config.get(
                "embedding_model", "sentence-transformers/all-MiniLM-L6-v2"
            )
            self._health.extra["db_url"] = str(db_url)[:80] if db_url else "(none)"
            self._health.extra["namespace"] = self._namespace
        except Exception as e:
            self._health.healthy = False
            self._health.error_message = (
                f"Hindsight init failed: {type(e).__name__}: {str(e)[:300]}"
            )
            self._engine = None

    def _ensure_bank(self) -> Optional[str]:
        """Ensure a Hindsight bank exists for this scope. Returns bank_id.

        G5 Loop 4 fix: Hindsight 0.6.x has no public `create_bank` method.
        Banks are created implicitly via `get_bank_profile(bank_id,
        create_if_missing=True)`. The Loop 3 code called
        `list_banks(context=...)` with the wrong kwarg name (`context`
        instead of `request_context`) AND assumed sync; it now uses the
        sync wrapper `get_bank_profile` with `request_context=`.
        """
        if not self._engine or not self._health.healthy:
            return None
        if self._bank_id:
            return self._bank_id
        try:
            from hindsight_api import RequestContext  # type: ignore

            ctx = RequestContext(internal=True)
            # G5 Loop 4: use the persistent event loop so DB pools stay bound.
            profile = self._loop.run_until_complete(
                self._engine.get_bank_profile(
                    self._namespace, request_context=ctx, create_if_missing=True
                )
            )
            if profile is not None:
                self._bank_id = self._namespace
            return self._bank_id
        except Exception as e:
            # G5 HONEST-Mem: ensure failures are recorded centrally
            self._health.extra["ensure_bank_error"] = (
                f"{type(e).__name__}: {str(e)[:200]}"
            )
            return None

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        """G5 Loop 4: real ingestion via `engine.retain()` returning real
        memory_unit_ids. The Loop-2/3 synthetic-SHA1 ID hack is gone.
        """
        t0 = time.time()
        if not self._engine or not self._health.healthy:
            self._record_op("add", error=True)
            return []
        text = self.extract_substantive_text(turns, max_chars=2000)
        if not text.strip():
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            return []
        substantive = len(text) >= 100
        try:
            from hindsight_api import RequestContext  # type: ignore

            ctx = RequestContext(internal=True)
            bank_id = self._ensure_bank()
            if not bank_id:
                # _ensure_bank failed; surface as HONEST error
                self._record_op("add", latency_ms=(time.time() - t0) * 1000, error=True)
                self._record_error(
                    "hindsight.add",
                    f"ensure_bank returned None: {self._health.extra.get('ensure_bank_error', 'unknown')}",
                )
                return []
            # G5 Loop 4: call retain_async via our persistent loop. We
            # DO NOT call the sync `engine.retain()` wrapper because it
            # internally invokes asyncio.run(), which would race with
            # our long-lived loop's DB pools.
            ids = self._loop.run_until_complete(
                self._engine.retain_async(
                    bank_id=bank_id,
                    content=text,
                    context=f"phd-loop4 scope={self.merged_scope(self.scope, scope)}",
                    request_context=ctx,
                )
            ) or []
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            # HONEST-Mem: substantive input but zero ids returned == silent failure
            if substantive and not ids:
                self._record_error(
                    "hindsight.add",
                    "engine.retain returned no ids on substantive input",
                    silent_extraction=True,
                )
                return []
            # Refresh n_memories best-effort via bank stats
            try:
                stats = self._loop.run_until_complete(
                    self._engine.get_bank_stats(bank_id, request_context=ctx)
                )
                if isinstance(stats, dict):
                    n = stats.get("memory_unit_count") or stats.get("memory_count") or 0
                    self._health.n_memories = int(n)
            except Exception:
                # Don't surface a sentinel; leave previous count
                pass
            return [str(mid) for mid in ids]
        except Exception as e:
            self._record_op("add", latency_ms=(time.time() - t0) * 1000, error=True)
            self._record_error("hindsight.add", f"{type(e).__name__}: {e}")
            return []

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        t0 = time.time()
        if not self._engine or not self._health.healthy:
            self._record_op("search", error=True)
            return []
        try:
            bank_id = self._ensure_bank()
            if not bank_id:
                self._record_op("search", latency_ms=(time.time() - t0) * 1000, error=True)
                self._record_error(
                    "hindsight.search",
                    f"ensure_bank returned None: {self._health.extra.get('ensure_bank_error', 'unknown')}",
                )
                return []
            # G5 Loop 4: use recall_async via our persistent loop
            res, _trace = self._loop.run_until_complete(
                self._engine.recall_async(
                    bank_id=bank_id,
                    query=query,
                    fact_type="experience",
                    max_tokens=2048,
                )
            )
            self._record_op("search", latency_ms=(time.time() - t0) * 1000)
            out: List[Memory] = []
            for r in (res or [])[:k]:
                if isinstance(r, dict):
                    text = r.get("text") or r.get("content") or str(r)[:500]
                    rid = r.get("id") or r.get("memory_unit_id") or hashlib.sha1(str(text).encode()).hexdigest()[:16]
                    score = float(r.get("score", 0.0))
                else:
                    text = str(r)[:500]
                    rid = hashlib.sha1(str(text).encode()).hexdigest()[:16]
                    score = 0.0
                out.append(
                    Memory(
                        memory_id=str(rid),
                        text=text,
                        score=score,
                        scope=self.merged_scope(self.scope, scope),
                        state="active",
                        metadata={"backend": self.backend_name},
                    )
                )
            return out
        except Exception as e:
            self._record_op("search", latency_ms=(time.time() - t0) * 1000, error=True)
            self._record_error("hindsight.search", f"{type(e).__name__}: {e}")
            return []

    def clear(self) -> None:
        if not self._engine or not self._bank_id:
            return
        try:
            from hindsight_api import RequestContext  # type: ignore
            ctx = RequestContext(internal=True)
            # clear_observations is async; use our persistent loop
            self._loop.run_until_complete(
                self._engine.clear_observations(bank_id=self._bank_id, request_context=ctx)
            )
            self._health.n_memories = 0
        except Exception:
            pass

    def close(self) -> None:
        """Close the engine and shut down the persistent event loop."""
        try:
            if self._engine and hasattr(self._engine, "close"):
                close_attr = getattr(self._engine, "close", None)
                if close_attr is not None:
                    import inspect as ins
                    if ins.iscoroutinefunction(close_attr):
                        self._loop.run_until_complete(close_attr())
                    else:
                        close_attr()
        except Exception:
            pass
        try:
            if self._loop and not self._loop.is_closed():
                self._loop.close()
        except Exception:
            pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
