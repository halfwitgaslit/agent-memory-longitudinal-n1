"""Governed Cross-worktree Memory Propagation (GCMP).

Extends Letta Code MemFS (Feb 2026) with three explicit policy primitives:
1. InheritancePolicy — selective parent→child injection at fork
2. CrossQueryPolicy  — live cross-worktree querying from a parent orchestrator
3. PromotionPolicy   — per-fact calibrated promotion thresholds

See architecture/v1.md §4.4.
"""

from .cross_worktree import (
    CrossQueryPolicy,
    DEFAULT_INHERITANCE_POLICY,
    DEFAULT_PROMOTION_POLICY,
    DEFAULT_CROSS_QUERY_POLICY,
    ForkContext,
    GCMPManager,
    InheritancePolicy,
    PromotionPolicy,
    WorktreeMemoryView,
)

__all__ = [
    "CrossQueryPolicy",
    "DEFAULT_CROSS_QUERY_POLICY",
    "DEFAULT_INHERITANCE_POLICY",
    "DEFAULT_PROMOTION_POLICY",
    "ForkContext",
    "GCMPManager",
    "InheritancePolicy",
    "PromotionPolicy",
    "WorktreeMemoryView",
]
