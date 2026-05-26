"""NullBackend: the no-memory negative control."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from adapters.schema import Turn
from .base import Memory, MemoryBackend


class NullBackend(MemoryBackend):
    """Returns no memories. Used as the no-memory baseline arm."""

    backend_name = "null"

    def __init__(self, config: Optional[Dict[str, Any]] = None, scope: Optional[Dict[str, Any]] = None):
        super().__init__(config, scope)
        self._health.healthy = True
        self._health.embedding_model = "none"

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        # No-op; record latency for fair comparison
        t0 = time.time()
        self._record_op("add", latency_ms=(time.time() - t0) * 1000)
        return []

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        t0 = time.time()
        self._record_op("search", latency_ms=(time.time() - t0) * 1000)
        return []

    def clear(self) -> None:
        pass
