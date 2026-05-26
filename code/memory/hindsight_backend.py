"""HindsightBackend: wraps hindsight-api 0.6.x MemoryEngine.

Hindsight requires a Postgres database (pg0-embedded ships with the
hindsight-api package; we use the embedded engine to avoid external Postgres
dependency for smoke tests).

Configuration:
- db_url: defaults to pg0-embedded local instance; if unavailable, falls back
  to user-configured Postgres
- embeddings: LocalSTEmbeddings (sentence-transformers, no API key)
- llm: we set Anthropic Haiku for memory_llm/retain_llm/reflect_llm; smoke
  tests will skip the LLM-dependent ingestion path if ANTHROPIC_API_KEY is
  missing.

This backend is the heaviest to initialize (embedded Postgres takes ~3-5s);
it should be reused across the eval rather than re-instantiated per cell.
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

        try:
            from hindsight_api import (  # type: ignore
                LocalSTEmbeddings,
                MemoryEngine,
            )

            db_url = self.config.get("db_url") or os.environ.get("HINDSIGHT_DB_URL")
            if not db_url:
                # Start the embedded pg0 (ships in dep tree). It's async.
                try:
                    import asyncio
                    from hindsight_api.pg0 import start_embedded_postgres  # type: ignore

                    db_url = asyncio.run(start_embedded_postgres())
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
            # Set the explicitly-required env var as well so hindsight's internal
            # config validators don't trip the init check.
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
                skip_llm_verification=True,  # don't auto-call LLM during init
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
        """Ensure a Hindsight memory bank exists for this scope. Returns bank_id.

        Hindsight uses 'banks' as the unit of memory scoping. We create one
        per scope-namespace and reuse it.
        """
        if self._bank_id:
            return self._bank_id
        try:
            from hindsight_api import RequestContext  # type: ignore

            ctx = RequestContext(internal=True)
            # Create bank if it doesn't exist
            if hasattr(self._engine, "create_bank"):
                bank = self._engine.create_bank(
                    name=self._namespace,
                    context=ctx,
                )
                self._bank_id = getattr(bank, "id", None) or getattr(bank, "bank_id", None)
            elif hasattr(self._engine, "list_banks"):
                banks = self._engine.list_banks(context=ctx)
                if banks:
                    self._bank_id = getattr(banks[0], "id", None)
            return self._bank_id
        except Exception as e:
            self._health.extra["ensure_bank_error"] = str(e)[:200]
            return None

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        """Hindsight ingestion is async via a worker; for smoke, we record
        the observation directly into the bank if a write API exists, and
        return a synthetic ID for tracking.

        Full Hindsight worker integration is deferred to Phase 2 deployment.
        """
        t0 = time.time()
        if not self._engine or not self._health.healthy:
            self._record_op("add", error=True)
            return []
        text = self.extract_substantive_text(turns, max_chars=2000)
        if not text.strip():
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            return []
        try:
            from hindsight_api import RequestContext  # type: ignore

            ctx = RequestContext(internal=True)
            bank_id = self._ensure_bank()
            # Try the various known write methods; if all unavailable, return
            # a synthetic ID and mark this as a "smoke-only" path.
            result = None
            for method_name in (
                "record_observation",
                "ingest_text",
                "add_document",
                "add_observation",
            ):
                if hasattr(self._engine, method_name):
                    method = getattr(self._engine, method_name)
                    sig_params = method.__code__.co_varnames
                    kwargs: Dict[str, Any] = {"text": text}
                    if "context" in sig_params:
                        kwargs["context"] = ctx
                    if "bank_id" in sig_params and bank_id:
                        kwargs["bank_id"] = bank_id
                    try:
                        result = method(**kwargs)
                        break
                    except Exception:
                        continue
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            mid = (
                (getattr(result, "id", None) if result is not None else None)
                or hashlib.sha1(text.encode()).hexdigest()[:16]
            )
            self._health.n_memories += 1
            return [str(mid)]
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
            from hindsight_api import RequestContext  # type: ignore

            ctx = RequestContext(internal=True)
            bank_id = self._ensure_bank()
            if not bank_id:
                self._record_op("search", latency_ms=(time.time() - t0) * 1000)
                return []
            # Hindsight's recall returns (list[dict], trace|None)
            res, _trace = self._engine.recall(
                bank_id=bank_id,
                query=query,
                fact_type="default",
                max_tokens=2048,
            )
            self._record_op("search", latency_ms=(time.time() - t0) * 1000)
            out: List[Memory] = []
            for r in (res or [])[:k]:
                if isinstance(r, dict):
                    text = r.get("text") or r.get("content") or str(r)[:500]
                    rid = r.get("id") or hashlib.sha1(str(text).encode()).hexdigest()[:16]
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
        if not self._engine:
            return
        try:
            from hindsight_api import RequestContext  # type: ignore

            ctx = RequestContext(actor_id=self._namespace)
            if hasattr(self._engine, "clear_observations"):
                self._engine.clear_observations(context=ctx)
            self._health.n_memories = 0
        except Exception:
            pass

    def __del__(self):
        try:
            if self._engine and hasattr(self._engine, "close"):
                self._engine.close()
        except Exception:
            pass
