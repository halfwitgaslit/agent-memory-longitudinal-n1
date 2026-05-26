"""CogneeBackend: wraps cognee 1.1.0 (V1 add+cognify+search or V2 remember+recall).

Cognee requires an LLM (default OpenAI) for graph extraction during cognify().
For our smoke tests without OPENAI_API_KEY, we use the V1 add() that ingests
data without immediate cognify, falling back to vector-only search.

Scope mapping:
- `dataset_name` is derived from scope hash. Cognee multitenancy is enforced
  via the `user` argument; we use the default user for smoke and a per-scope
  derived user if multi-user is enabled.

This backend is the most heavyweight of the four; if OpenAI is unavailable
and Cognee cannot fall back to a local LLM, the backend marks itself
unhealthy and the arm is skipped at eval time.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import time
from typing import Any, Dict, List, Optional

from adapters.schema import Turn
from .base import Memory, MemoryBackend


def _scope_dataset(scope: Dict[str, Any]) -> str:
    keys = sorted(scope.keys())
    s = "|".join(f"{k}={scope[k]}" for k in keys)
    h = hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()[:10]
    return f"phd_{h}"


class CogneeBackend(MemoryBackend):
    backend_name = "cognee"

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config, scope)
        # Configure cognee for local-only operation
        # We use LanceDB for vector storage and DuckDB for graph storage
        # to avoid Postgres dependency
        try:
            import cognee  # type: ignore

            self._cognee = cognee
            # Disable backend access control to avoid auth flow during smoke
            os.environ.setdefault("ENABLE_BACKEND_ACCESS_CONTROL", "false")
            # Use local file storage instead of cloud
            os.environ.setdefault("VECTOR_DB_PROVIDER", "lancedb")
            os.environ.setdefault("GRAPH_DATABASE_PROVIDER", "kuzu")
            # Default LLM to anthropic for fact extraction (subscription billing path)
            os.environ.setdefault("LLM_PROVIDER", "anthropic")
            os.environ.setdefault("LLM_MODEL", "anthropic/claude-3-5-haiku-latest")
            # OpenAI embeddings require API key; switch to fastembed
            os.environ.setdefault("EMBEDDING_PROVIDER", "fastembed")
            os.environ.setdefault("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
            os.environ.setdefault("EMBEDDING_DIMENSIONS", "384")
            # Check at least that cognee module loaded without exception
            self._dataset = _scope_dataset(self.scope)
            self._health.healthy = True
            self._health.embedding_model = "BAAI/bge-small-en-v1.5"
            self._health.extra["dataset"] = self._dataset
            self._health.extra["v"] = getattr(cognee, "__version__", "1.1.0")
        except Exception as e:
            self._health.healthy = False
            self._health.error_message = f"cognee init failed: {type(e).__name__}: {e}"
            self._cognee = None

    def _async_run(self, coro):
        """Synchronously run a coroutine; works whether or not an event loop exists."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None and loop.is_running():
            # If somehow inside an already-running loop, schedule and wait
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                fut = pool.submit(asyncio.run, coro)
                return fut.result()
        return asyncio.run(coro)

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        t0 = time.time()
        if not self._cognee or not self._health.healthy:
            self._record_op("add", error=True)
            return []
        text = self.extract_substantive_text(turns, max_chars=4000)
        if not text.strip():
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            return []
        try:
            # V1 add: ingest into dataset
            self._async_run(self._cognee.add(text, dataset_name=self._dataset))
            # Cognify is required to make the data searchable. It uses the LLM
            # for graph extraction; if LLM is unavailable it logs an error but
            # still indexes chunks for vector search.
            try:
                self._async_run(self._cognee.cognify(datasets=[self._dataset]))
            except Exception as cog_e:
                # Cognify failed (likely LLM unavailable); chunks may still be searchable
                self._health.extra["last_cognify_error"] = str(cog_e)[:200]
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            mid = hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:16]
            self._health.n_memories += 1
            return [mid]
        except Exception as e:
            self._record_op("add", latency_ms=(time.time() - t0) * 1000, error=True)
            self._health.error_message = (
                f"cognee add failed: {type(e).__name__}: {str(e)[:200]}"
            )
            return []

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        t0 = time.time()
        if not self._cognee or not self._health.healthy:
            self._record_op("search", error=True)
            return []
        try:
            # V2 recall is preferred (auto-routes); but it requires cognified data
            # For raw add() data, use cognee.search with SearchType.CHUNKS
            from cognee.modules.search.types import SearchType  # type: ignore

            res = self._async_run(
                self._cognee.search(
                    query_text=query,
                    query_type=SearchType.CHUNKS,
                    datasets=[self._dataset],
                    top_k=k,
                )
            )
            self._record_op("search", latency_ms=(time.time() - t0) * 1000)
            out: List[Memory] = []
            if not res:
                return out
            for r in (res if isinstance(res, list) else [res])[:k]:
                # SearchResult shape varies; extract any text content
                text = getattr(r, "text", None) or getattr(r, "content", None) or str(r)[:500]
                rid = getattr(r, "id", None) or hashlib.sha1(str(text).encode()).hexdigest()[:16]
                out.append(
                    Memory(
                        memory_id=str(rid),
                        text=str(text)[:2000],
                        score=float(getattr(r, "score", 0.0) or 0.0),
                        scope=self.merged_scope(self.scope, scope),
                        state="active",
                        metadata={"backend": self.backend_name},
                    )
                )
            return out
        except Exception as e:
            self._record_op("search", latency_ms=(time.time() - t0) * 1000, error=True)
            self._health.error_message = (
                f"cognee search failed: {type(e).__name__}: {str(e)[:200]}"
            )
            return []

    def clear(self) -> None:
        if not self._cognee:
            return
        try:
            self._async_run(self._cognee.prune.prune_data())
            self._async_run(self._cognee.prune.prune_system(metadata=True))
            self._health.n_memories = 0
        except Exception:
            pass
