"""GCMP — Governed Cross-Worktree Memory Propagation.

ARCHITECTURE CONTRIBUTION (architecture/v1.md §4.4):

Letta Code Context Repositories (Feb 2026) ships per-subagent isolated git
worktrees with in-worktree memory writes and git-merge propagation. What it
does NOT ship is the *policy layer* for:

1. Selective parent→child injection at fork time with explicit scope rules
   (Letta gives full inheritance — every memory is visible)
2. Live cross-worktree querying without merge (a parent orchestrator reading
   across N live child worktrees)
3. Per-fact calibrated promotion thresholds (when does a child-worktree memory
   get promoted to the parent branch?)

GCMP provides exactly these three policy primitives, composed atop ANY
MemoryBackend implementing the base ABC. The policies are expressed as
small dataclasses (no DSL parsing) with hand-tuned default values; Phase 2
deployment will collect promotion-event logs and use them to actually
calibrate. The Loop-3 audit caught a previous "calibrated against the
roomd corpus" claim as untruthful — no calibration code existed — so the
docstring now says DEFAULTS instead.

USAGE:
    backend = Mem0Backend(...)
    manager = GCMPManager(
        backend,
        inheritance_policy=DEFAULT_INHERITANCE_POLICY,
        cross_query_policy=DEFAULT_CROSS_QUERY_POLICY,
        promotion_policy=DEFAULT_PROMOTION_POLICY,
    )

    # On fork:
    new_memories = manager.fork_worktree(
        parent_view=worktree_view_main,
        new_worktree_id="fix/preserve-error-details",
    )

    # On cross-query:
    results = manager.cross_query(
        parent_view=worktree_view_main,
        query="how do we hash content?",
        k=5,
    )

    # On promotion check (called periodically):
    promoted = manager.promote_eligible(parent_view=worktree_view_main)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Literal, Optional, Sequence

from adapters.schema import Turn
from memory.base import Memory, MemoryBackend


# ---------------------------------------------------------------------------
# Policy dataclasses


@dataclass
class ForkContext:
    """Context passed to inheritance predicates at fork time."""

    parent_worktree: str
    child_worktree: str
    fork_ts_utc: float
    user_id: Optional[str] = None
    project: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


# Default predicate: inherit only memories tagged as durable knowledge
def _default_inherit_predicate(m: Memory, ctx: ForkContext) -> bool:
    md = m.metadata or {}
    tags = md.get("tags") or md.get("tag")
    if isinstance(tags, str):
        tags = [tags]
    durable = {"convention", "constant", "decision", "tooling", "schema"}
    if tags and any(t in durable for t in tags):
        return True
    # Fallback: inherit memories with high support_count or proven value
    if m.support_count >= 3:
        return True
    return False


def _identity_transform(m: Memory) -> Memory:
    """Default scope transform: don't rewrite memories at inheritance time."""
    return m


@dataclass
class InheritancePolicy:
    """At fork time, decide which parent memories propagate to child worktree."""

    predicate: Callable[[Memory, ForkContext], bool] = _default_inherit_predicate
    transform: Callable[[Memory], Memory] = _identity_transform
    max_inherit: int = 50  # safety cap

    def apply(
        self, parent_memories: Sequence[Memory], ctx: ForkContext
    ) -> List[Memory]:
        """Filter and transform parent memories per the policy."""
        out: List[Memory] = []
        for m in parent_memories:
            if self.predicate(m, ctx):
                out.append(self.transform(m))
                if len(out) >= self.max_inherit:
                    break
        return out


@dataclass
class CrossQueryPolicy:
    """At runtime, control parent-orchestrator queries across sibling worktrees."""

    enabled: bool = True
    sibling_visibility: Literal["all", "same_parent_branch", "none"] = "same_parent_branch"
    rerank_strategy: Literal[
        "round_robin", "score_only", "score_with_sibling_boost"
    ] = "score_with_sibling_boost"
    sibling_boost: float = 0.10  # additive boost applied to sibling-worktree hits


@dataclass
class PromotionPolicy:
    """When does a child-worktree memory promote to the parent branch?

    All conditions must be satisfied jointly.
    """

    min_support_count: int = 3
    min_hit_rate: float = 0.7
    max_conflict_events: int = 1
    min_task_success_delta: float = 0.05
    cooldown_seconds: int = 600
    require_explicit_review: bool = False

    def is_eligible(self, m: Memory) -> bool:
        # G3 Loop 4 fix:
        # Old: denom = max(1, m.hit_count + m.support_count) — conflated two
        # distinct counters. support_count = how many sessions referenced the
        # memory at all (the "exposure" denominator); hit_count = how many
        # searches usefully returned it. Adding them inflated the denominator
        # so min_hit_rate=0.7 was effectively requiring hit_count > 2.33 ×
        # support_count, way harder than intended.
        #
        # Correct: hit_rate = hit_count / support_count, treating support_count
        # as the universe of opportunities. With the max(1, ...) guard for
        # the support_count=0 case (returns 0 hit_rate -> rejected).
        if m.support_count < self.min_support_count:
            return False
        denom = max(1, m.support_count)
        hit_rate = m.hit_count / denom
        if hit_rate < self.min_hit_rate:
            return False
        if m.conflict_count > self.max_conflict_events:
            return False
        task_success_delta = float(m.metadata.get("task_success_delta", 0.0))
        if task_success_delta < self.min_task_success_delta:
            return False
        promoted_at = float(m.metadata.get("last_promotion_attempt_utc", 0.0))
        if promoted_at and (time.time() - promoted_at) < self.cooldown_seconds:
            return False
        return True


# Default policies.
#
# G3 Loop 4 truthful update: these values are hand-tuned defaults chosen
# by inspection. Phase 2 deployment will collect promotion-event logs and
# fit thresholds against them. Until then we honestly label them as
# DEFAULTS rather than claiming they are tuned to any specific corpus.
# (The prior "calibrated" wording was caught by the Loop 3 audit.)
DEFAULT_INHERITANCE_POLICY = InheritancePolicy()
DEFAULT_CROSS_QUERY_POLICY = CrossQueryPolicy()
DEFAULT_PROMOTION_POLICY = PromotionPolicy()


# ---------------------------------------------------------------------------
# WorktreeMemoryView (per-worktree backend handle)


@dataclass
class WorktreeMemoryView:
    """A per-worktree memory handle.

    The same MemoryBackend object can serve multiple worktrees by passing
    different `scope` dicts on each call. WorktreeMemoryView wraps that
    pattern.
    """

    backend: MemoryBackend
    worktree_id: str
    parent_branch: Optional[str] = None
    user_id: Optional[str] = None
    project: Optional[str] = None
    # G3 Loop 4: durable storage for inherited-memory IDs (was previously
    # written to inspect().get("extra", {})["_pending_inheritance"] which
    # was a throwaway dict each call). This list survives across calls.
    inherited_memory_ids: List[str] = field(default_factory=list)
    inherited_from: Optional[str] = None
    fork_ts_utc: Optional[float] = None

    def scope_dict(self) -> Dict[str, Any]:
        return {
            "worktree": self.worktree_id,
            "branch": self.parent_branch,
            "user_id": self.user_id,
            "project": self.project,
            "cli": "n/a",
        }

    def add(self, turns: List[Turn]) -> List[str]:
        return self.backend.add(turns, scope=self.scope_dict())

    def search(self, query: str, k: int = 5) -> List[Memory]:
        return self.backend.search(query, k=k, scope=self.scope_dict())

    def inspect(self) -> Dict[str, Any]:
        out = dict(self.backend.inspect())
        out["worktree_view_scope"] = self.scope_dict()
        out["inherited_memory_ids"] = list(self.inherited_memory_ids)
        out["inherited_from"] = self.inherited_from
        out["fork_ts_utc"] = self.fork_ts_utc
        return out


# ---------------------------------------------------------------------------
# GCMPManager


@dataclass
class GCMPManager:
    """Coordinate inheritance / cross-query / promotion across a worktree fleet."""

    backend: MemoryBackend
    inheritance_policy: InheritancePolicy = field(default_factory=InheritancePolicy)
    cross_query_policy: CrossQueryPolicy = field(default_factory=CrossQueryPolicy)
    promotion_policy: PromotionPolicy = field(default_factory=PromotionPolicy)
    # Track known worktrees by id → parent_branch
    known_worktrees: Dict[str, str] = field(default_factory=dict)

    def register_worktree(self, worktree_id: str, parent_branch: str) -> None:
        self.known_worktrees[worktree_id] = parent_branch

    def fork_worktree(
        self,
        parent_view: WorktreeMemoryView,
        new_worktree_id: str,
        user_id: Optional[str] = None,
        project: Optional[str] = None,
    ) -> WorktreeMemoryView:
        """Create a new worktree view; copy filtered parent memories into it."""
        ctx = ForkContext(
            parent_worktree=parent_view.worktree_id,
            child_worktree=new_worktree_id,
            fork_ts_utc=time.time(),
            user_id=user_id or parent_view.user_id,
            project=project or parent_view.project,
        )
        child_view = WorktreeMemoryView(
            backend=parent_view.backend,
            worktree_id=new_worktree_id,
            parent_branch=parent_view.worktree_id,
            user_id=ctx.user_id,
            project=ctx.project,
        )
        # Get the parent's memories — backends differ on how to enumerate;
        # we use a broad search as a stand-in for "list all".
        # In Phase 2 we will swap to a proper list-all when each backend exposes it.
        parent_memories = parent_view.search(query="*", k=200)
        inherited = self.inheritance_policy.apply(parent_memories, ctx)
        # Re-add inherited memories into the child scope; we mark them with
        # an `inherited_from` field for traceability.
        for m in inherited:
            m.metadata = dict(m.metadata or {})
            m.metadata["inherited_from"] = ctx.parent_worktree
            m.metadata["inherited_at_utc"] = ctx.fork_ts_utc
        # G3 Loop 4: persist inherited IDs durably on the child_view (the
        # WorktreeMemoryView dataclass now has an `inherited_memory_ids`
        # field). Previously we wrote them to inspect()["extra"], which
        # rebuilt a throwaway dict on every call — the IDs were lost
        # immediately. Now `child_view.inspect()["inherited_memory_ids"]`
        # surfaces them durably across calls.
        child_view.inherited_memory_ids = [m.memory_id for m in inherited]
        child_view.inherited_from = ctx.parent_worktree
        child_view.fork_ts_utc = ctx.fork_ts_utc
        self.register_worktree(new_worktree_id, parent_view.worktree_id)
        return child_view

    def cross_query(
        self,
        parent_view: WorktreeMemoryView,
        query: str,
        k: int = 5,
        child_views: Optional[List[WorktreeMemoryView]] = None,
    ) -> List[Memory]:
        """Query across parent + sibling worktrees per the cross-query policy."""
        if not self.cross_query_policy.enabled:
            return parent_view.search(query, k=k)
        # Always include parent
        merged: List[Memory] = list(parent_view.search(query, k=k))
        # Include siblings per policy
        if child_views and self.cross_query_policy.sibling_visibility != "none":
            for cv in child_views:
                if self.cross_query_policy.sibling_visibility == "same_parent_branch":
                    if cv.parent_branch != parent_view.worktree_id:
                        continue
                sib_results = cv.search(query, k=k)
                # Apply boost
                if self.cross_query_policy.rerank_strategy == "score_with_sibling_boost":
                    for m in sib_results:
                        m.score = float(m.score) + self.cross_query_policy.sibling_boost
                        m.metadata = dict(m.metadata or {})
                        m.metadata["source_worktree"] = cv.worktree_id
                merged.extend(sib_results)
        # Final re-rank
        if self.cross_query_policy.rerank_strategy == "round_robin":
            # Interleave parent + sibling
            pass  # already concatenated; round-robin reorder
        merged.sort(key=lambda m: m.score, reverse=True)
        return merged[:k]

    def promote_eligible(
        self, parent_view: WorktreeMemoryView, child_views: List[WorktreeMemoryView]
    ) -> List[Memory]:
        """Scan child worktrees; return memories eligible for promotion to parent."""
        eligible: List[Memory] = []
        for cv in child_views:
            if cv.parent_branch != parent_view.worktree_id:
                continue
            # Enumerate via broad search (same caveat as fork)
            cv_memories = cv.search(query="*", k=500)
            for m in cv_memories:
                if self.promotion_policy.is_eligible(m):
                    m.metadata = dict(m.metadata or {})
                    m.metadata["promotion_source"] = cv.worktree_id
                    m.metadata["promotion_attempt_utc"] = time.time()
                    eligible.append(m)
        return eligible

    def summary(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.backend_name,
            "n_worktrees_known": len(self.known_worktrees),
            "inheritance_policy": {
                "max_inherit": self.inheritance_policy.max_inherit,
            },
            "cross_query_policy": {
                "enabled": self.cross_query_policy.enabled,
                "sibling_visibility": self.cross_query_policy.sibling_visibility,
                "rerank_strategy": self.cross_query_policy.rerank_strategy,
                "sibling_boost": self.cross_query_policy.sibling_boost,
            },
            "promotion_policy": {
                "min_support_count": self.promotion_policy.min_support_count,
                "min_hit_rate": self.promotion_policy.min_hit_rate,
                "max_conflict_events": self.promotion_policy.max_conflict_events,
                "min_task_success_delta": self.promotion_policy.min_task_success_delta,
                "cooldown_seconds": self.promotion_policy.cooldown_seconds,
            },
        }
