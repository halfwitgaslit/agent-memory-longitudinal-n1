"""Base ABC for memory backends.

The contract is intentionally minimal so that each underlying system (Mem0,
Letta, Hindsight, Cognee, ...) can be wrapped without forcing all to share
implementation strategy. The methods are:

- add(turns)       : store/extract memories from a list of unified Turns
- search(query, k) : retrieve top-k memories for a query
- inspect()        : return diagnostic info (counts, latencies, health)
- decay_step()     : apply decay rules and report counts updated
- lifecycle_promote(id, new_state) : explicit state transition (used by PDDC/GCMP)
- clear()          : wipe all memories (used between eval cells)

Scope: a free-form dict that disambiguates per-deployment / per-worktree /
per-cli memory partitions. Reserved keys: user_id, project, worktree, branch,
cli. Backends are free to ignore keys they don't honor (e.g., NullBackend).
"""

from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Late import to avoid circular dependency
from adapters.schema import Turn


class Memory(BaseModel):
    """A retrieved memory (one item in search results)."""

    model_config = ConfigDict(extra="allow")
    memory_id: str
    text: str
    score: float = 0.0
    scope: Dict[str, Any] = Field(default_factory=dict)
    state: str = "active"  # one of: draft, active, deprecated, archived (per PDDC FSM)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_utc: float = 0.0
    last_seen_utc: float = 0.0
    support_count: int = 0
    hit_count: int = 0
    conflict_count: int = 0


@dataclass
class BackendHealth:
    """Per-backend health snapshot."""

    backend_name: str
    healthy: bool
    error_message: Optional[str] = None
    embedding_model: Optional[str] = None
    n_memories: int = 0
    cumulative_latency_ms: float = 0.0
    n_searches: int = 0
    n_adds: int = 0
    n_errors: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


class MemoryBackend(abc.ABC):
    """Abstract base for all memory backends."""

    backend_name: str = "abstract"

    def __init__(self, config: Optional[Dict[str, Any]] = None, scope: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.scope = scope or {}
        self._health = BackendHealth(backend_name=self.backend_name, healthy=False)
        self._call_count = 0
        self._t_start = time.time()

    # ------------------------------------------------------------------
    # Core operations

    @abc.abstractmethod
    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        """Store memories derived from a list of unified Turns.

        Returns a list of newly-created memory_ids (may be empty if backend
        deduplicates or filters out non-substantive content).
        """

    @abc.abstractmethod
    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        """Return top-k memories for the query, scoped if applicable."""

    def inspect(self) -> Dict[str, Any]:
        """Return a serializable health/diagnostic snapshot."""
        return {
            "backend_name": self.backend_name,
            "healthy": self._health.healthy,
            "error_message": self._health.error_message,
            "embedding_model": self._health.embedding_model,
            "n_memories": self._health.n_memories,
            "cumulative_latency_ms": self._health.cumulative_latency_ms,
            "n_searches": self._health.n_searches,
            "n_adds": self._health.n_adds,
            "n_errors": self._health.n_errors,
            "uptime_s": time.time() - self._t_start,
            "scope": self.scope,
            "extra": self._health.extra,
        }

    def decay_step(self, now_utc: Optional[float] = None) -> Dict[str, int]:
        """Apply decay/lifecycle transitions. Default implementation: no-op.

        Override to integrate with calibration/decay.py PDDC.
        """
        return {"n_updated": 0, "n_promoted": 0, "n_archived": 0}

    def lifecycle_promote(self, memory_id: str, new_state: str) -> bool:
        """Transition a memory to a new lifecycle state. Default: returns False."""
        return False

    def clear(self) -> None:
        """Wipe all memories. Default: no-op (subclasses override)."""

    # ------------------------------------------------------------------
    # Convenience helpers

    def _record_op(self, kind: str, latency_ms: float = 0.0, error: bool = False) -> None:
        if kind == "search":
            self._health.n_searches += 1
        elif kind == "add":
            self._health.n_adds += 1
        if error:
            self._health.n_errors += 1
        self._health.cumulative_latency_ms += latency_ms

    @staticmethod
    def merged_scope(
        base: Optional[Dict[str, Any]], override: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        s = dict(base or {})
        if override:
            s.update(override)
        return s

    @staticmethod
    def extract_substantive_text(turns: List[Turn], max_chars: int = 8000) -> str:
        """Concatenate substantive text from a list of Turns for memory extraction.

        Strips thinking blocks (which are model-internal), preserves user/assistant
        text and a compact summary of tool calls.
        """
        out: List[str] = []
        total = 0
        for t in turns:
            role_tag = f"[{t.role}]"
            for cb in t.content:
                if cb.kind == "text" and cb.text:
                    chunk = f"{role_tag} {cb.text}\n"
                    out.append(chunk)
                    total += len(chunk)
                elif cb.kind == "tool_use" and cb.name:
                    chunk = f"{role_tag} <tool_use name={cb.name}>\n"
                    out.append(chunk)
                    total += len(chunk)
                elif cb.kind == "tool_result" and cb.output:
                    # truncate large outputs
                    snippet = cb.output[:500]
                    chunk = f"{role_tag} <tool_result>{snippet}\n"
                    out.append(chunk)
                    total += len(chunk)
                if total >= max_chars:
                    return "".join(out)[:max_chars]
        return "".join(out)
