"""RandomBackend: returns k randomly-chosen previously-added memories.

This is the second negative control. The point: any backend that does better
than RandomBackend is doing *some* form of useful retrieval; any backend that
loses to RandomBackend is anti-helpful (a known failure mode for badly-tuned
embeddings on small corpora).
"""

from __future__ import annotations

import random
import time
import uuid
from typing import Any, Dict, List, Optional

from adapters.schema import Turn
from .base import Memory, MemoryBackend


class RandomBackend(MemoryBackend):
    backend_name = "random"

    def __init__(self, config: Optional[Dict[str, Any]] = None, scope: Optional[Dict[str, Any]] = None):
        super().__init__(config, scope)
        seed = (config or {}).get("seed", 42)
        self._rng = random.Random(seed)
        self._memories: List[Memory] = []
        self._health.healthy = True
        self._health.embedding_model = "none"

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        t0 = time.time()
        text = self.extract_substantive_text(turns, max_chars=2000)
        # one memory per add() call; truncated for stable comparison footprint
        if not text.strip():
            self._record_op("add", latency_ms=(time.time() - t0) * 1000)
            return []
        mid = uuid.uuid4().hex[:16]
        m = Memory(
            memory_id=mid,
            text=text,
            score=0.0,
            scope=self.merged_scope(self.scope, scope),
            state="active",
            metadata={"backend": self.backend_name},
            created_utc=time.time(),
            last_seen_utc=time.time(),
            support_count=1,
        )
        self._memories.append(m)
        self._health.n_memories = len(self._memories)
        self._record_op("add", latency_ms=(time.time() - t0) * 1000)
        return [mid]

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        t0 = time.time()
        if not self._memories:
            self._record_op("search", latency_ms=(time.time() - t0) * 1000)
            return []
        n = min(k, len(self._memories))
        chosen = self._rng.sample(self._memories, n)
        # assign uniform random scores in [0, 1)
        for m in chosen:
            m.score = self._rng.random()
            m.hit_count += 1
            m.last_seen_utc = time.time()
        self._record_op("search", latency_ms=(time.time() - t0) * 1000)
        return chosen

    def clear(self) -> None:
        self._memories.clear()
        self._health.n_memories = 0
