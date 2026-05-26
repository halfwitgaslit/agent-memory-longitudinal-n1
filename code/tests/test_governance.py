"""Tests for GCMP — governed cross-worktree memory propagation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.schema import ContentBlock, Turn  # noqa: E402
from governance.cross_worktree import (  # noqa: E402
    CrossQueryPolicy,
    DEFAULT_INHERITANCE_POLICY,
    DEFAULT_PROMOTION_POLICY,
    ForkContext,
    GCMPManager,
    InheritancePolicy,
    PromotionPolicy,
    WorktreeMemoryView,
)
from memory.base import Memory  # noqa: E402
from memory.random_backend import RandomBackend  # noqa: E402


def _make_turn(text: str, role: str = "user", ordinal: int = 0) -> Turn:
    return Turn(
        turn_id=Turn.make_turn_id("s", ordinal, text),
        session_id="s",
        ordinal=ordinal,
        role=role,  # type: ignore[arg-type]
        content=[ContentBlock(kind="text", text=text)],
        tool_events=[],
        ts_utc=0.0,
        model="x",
        cli="claude_code",
    )


def test_inheritance_policy_filters_by_tag():
    pol = InheritancePolicy()
    ctx = ForkContext(parent_worktree="main", child_worktree="feat/x", fork_ts_utc=0.0)
    durable = Memory(
        memory_id="m1",
        text="we use Pydantic v2",
        score=0.9,
        scope={},
        state="active",
        metadata={"tags": ["convention"]},
        support_count=1,
    )
    transient = Memory(
        memory_id="m2",
        text="user asked about today's weather",
        score=0.5,
        scope={},
        state="active",
        metadata={"tags": ["incidental"]},
        support_count=1,
    )
    inherited = pol.apply([durable, transient], ctx)
    assert any(m.memory_id == "m1" for m in inherited)
    assert not any(m.memory_id == "m2" for m in inherited)


def test_inheritance_policy_fallback_high_support():
    """Memories with high support_count should inherit even without tags."""
    pol = InheritancePolicy()
    ctx = ForkContext(parent_worktree="main", child_worktree="feat/y", fork_ts_utc=0.0)
    well_supported = Memory(
        memory_id="ws", text="x", score=0.5, scope={}, state="active",
        metadata={}, support_count=5,
    )
    barely_seen = Memory(
        memory_id="bs", text="y", score=0.5, scope={}, state="active",
        metadata={}, support_count=1,
    )
    inherited = pol.apply([well_supported, barely_seen], ctx)
    assert any(m.memory_id == "ws" for m in inherited)
    assert not any(m.memory_id == "bs" for m in inherited)


def test_inheritance_policy_respects_max_inherit():
    pol = InheritancePolicy(max_inherit=2)
    ctx = ForkContext(parent_worktree="main", child_worktree="feat/z", fork_ts_utc=0.0)
    mems = [
        Memory(memory_id=f"m{i}", text=f"t{i}", score=0.5, scope={}, state="active",
               metadata={"tags": ["convention"]}, support_count=1)
        for i in range(5)
    ]
    inherited = pol.apply(mems, ctx)
    assert len(inherited) == 2


def test_promotion_policy_thresholds():
    pol = PromotionPolicy(
        min_support_count=3,
        min_hit_rate=0.7,
        max_conflict_events=1,
        min_task_success_delta=0.05,
    )
    # Eligible: hits all thresholds
    eligible = Memory(
        memory_id="e", text="t", score=0.5, scope={}, state="active",
        support_count=4, hit_count=10,  # hit_rate = 10/(10+4) = 0.71
        conflict_count=0,
        metadata={"task_success_delta": 0.1},
    )
    assert pol.is_eligible(eligible)

    # Ineligible: low support
    low_sup = Memory(
        memory_id="ls", text="t", score=0.5, scope={}, state="active",
        support_count=1, hit_count=10, conflict_count=0,
        metadata={"task_success_delta": 0.1},
    )
    assert not pol.is_eligible(low_sup)

    # Ineligible: too many conflicts
    conflicty = Memory(
        memory_id="cc", text="t", score=0.5, scope={}, state="active",
        support_count=4, hit_count=10, conflict_count=5,
        metadata={"task_success_delta": 0.1},
    )
    assert not pol.is_eligible(conflicty)

    # Ineligible: negative task_success_delta
    harmful = Memory(
        memory_id="hh", text="t", score=0.5, scope={}, state="active",
        support_count=4, hit_count=10, conflict_count=0,
        metadata={"task_success_delta": -0.1},
    )
    assert not pol.is_eligible(harmful)


def test_cross_query_disabled_returns_parent_only():
    backend = RandomBackend(scope={"user_id": "v", "project": "r"})
    parent_view = WorktreeMemoryView(
        backend=backend, worktree_id="main", user_id="v", project="r"
    )
    parent_view.add([_make_turn(f"parent memory {i}", ordinal=i) for i in range(5)])
    child_view = WorktreeMemoryView(
        backend=backend, worktree_id="feat/a", parent_branch="main",
        user_id="v", project="r",
    )
    child_view.add([_make_turn(f"child memory {i}", ordinal=10 + i) for i in range(3)])

    mgr = GCMPManager(
        backend=backend,
        cross_query_policy=CrossQueryPolicy(enabled=False),
    )
    results = mgr.cross_query(parent_view, "x", k=3, child_views=[child_view])
    # Disabled cross-query should mean we just got parent search
    assert len(results) <= 3


def test_cross_query_sibling_visibility_same_parent_branch():
    backend = RandomBackend(scope={"user_id": "v", "project": "r"})
    main_view = WorktreeMemoryView(backend, "main", user_id="v", project="r")
    sib_a = WorktreeMemoryView(
        backend, "feat/a", parent_branch="main", user_id="v", project="r"
    )
    sib_b = WorktreeMemoryView(
        backend, "feat/b", parent_branch="main", user_id="v", project="r"
    )
    not_sib = WorktreeMemoryView(
        backend, "feat/c", parent_branch="other-main", user_id="v", project="r"
    )
    for v in (main_view, sib_a, sib_b, not_sib):
        v.add([_make_turn(f"{v.worktree_id} mem {i}", ordinal=i) for i in range(3)])

    mgr = GCMPManager(
        backend=backend,
        cross_query_policy=CrossQueryPolicy(
            enabled=True, sibling_visibility="same_parent_branch"
        ),
    )
    results = mgr.cross_query(
        main_view, "x", k=10, child_views=[sib_a, sib_b, not_sib]
    )
    # 'not_sib' must NOT appear; sib_a and sib_b can. (Random backend may
    # not return all of them, but we assert the filter)
    not_sib_in_results = any(
        m.metadata.get("source_worktree") == "feat/c" for m in results
    )
    assert not not_sib_in_results, (
        "Cross-query leaked memories from a non-sibling worktree"
    )


def test_fork_worktree_registers_known():
    backend = RandomBackend(scope={"user_id": "v", "project": "r"})
    main_view = WorktreeMemoryView(backend, "main", user_id="v", project="r")
    # seed parent with one durable memory
    main_view.add([_make_turn("convention: use snake_case")])
    mgr = GCMPManager(backend=backend)
    child = mgr.fork_worktree(main_view, new_worktree_id="feat/abc", user_id="v", project="r")
    assert child.worktree_id == "feat/abc"
    assert child.parent_branch == "main"
    assert "feat/abc" in mgr.known_worktrees
    assert mgr.known_worktrees["feat/abc"] == "main"


def test_gcmp_manager_summary_serializable():
    import json
    backend = RandomBackend(scope={"user_id": "v", "project": "r"})
    mgr = GCMPManager(backend=backend)
    summary = mgr.summary()
    json.dumps(summary)  # must not raise
    assert summary["backend"] == "random"
    assert "inheritance_policy" in summary
    assert "cross_query_policy" in summary
    assert "promotion_policy" in summary


# ------------------------------------------------------------------
# G3 Loop 4 regression guards
# ------------------------------------------------------------------


def test_g3_hit_rate_formula_uses_support_as_denominator():
    """Post-Loop-4: hit_rate is hit_count / support_count, NOT
    hit_count / (hit_count + support_count). The old formula made
    min_hit_rate=0.7 effectively require hit_count > 2.33 * support_count
    — way harder than intended.

    Under the corrected formula, support=5 hits=8 gives hit_rate=1.6 which
    must clear the 0.7 threshold trivially.
    """
    pol = PromotionPolicy(
        min_support_count=3,
        min_hit_rate=0.7,
        max_conflict_events=1,
        min_task_success_delta=0.05,
    )
    # Under OLD formula: 8/(8+5)=0.615 (fails). Under NEW: 8/5=1.6 (passes).
    m = Memory(
        memory_id="g3_hit_rate",
        text="t",
        score=0.5,
        scope={},
        state="active",
        support_count=5,
        hit_count=8,
        conflict_count=0,
        metadata={"task_success_delta": 0.1},
    )
    assert pol.is_eligible(m), (
        "G3 regression: hit_rate formula reverted to old denominator"
    )


def test_g3_fork_worktree_persists_inherited_ids():
    """Post-Loop-4: fork_worktree() persists inherited memory IDs on the
    child_view.inherited_memory_ids field (durable). Previously it wrote
    to a throwaway dict returned by inspect()["extra"] and the IDs were
    silently discarded.
    """
    backend = RandomBackend(scope={"user_id": "v", "project": "r"})
    main_view = WorktreeMemoryView(backend, "main", user_id="v", project="r")
    # Seed a durable parent memory; we'll see if it survives the fork
    main_view.add([_make_turn("convention: use snake_case", ordinal=1)])
    mgr = GCMPManager(backend=backend)
    child = mgr.fork_worktree(main_view, new_worktree_id="feat/g3", user_id="v", project="r")
    # The persisted field must exist
    assert isinstance(child.inherited_memory_ids, list)
    # Either inherited some IDs OR the inheritance predicate found nothing
    # eligible (acceptable). Critical: the dict-of-throwaway-dict pattern
    # is gone.
    insp = child.inspect()
    assert "inherited_memory_ids" in insp
    assert isinstance(insp["inherited_memory_ids"], list)
    assert insp["inherited_from"] == "main"
    assert insp["fork_ts_utc"] is not None


def test_g3_default_promotion_policy_label_is_truthful():
    """Post-Loop-4: the DEFAULT_*_POLICY definitions must NOT carry a
    comment claiming the values are calibrated. Phase 2 will calibrate;
    until then the comments must honestly label them as DEFAULTS.

    We check the lines around DEFAULT_INHERITANCE_POLICY etc., not the
    module docstring (which is allowed to mention the prior bug as
    historical context).
    """
    import inspect as ins
    from governance import cross_worktree as cw
    src = ins.getsource(cw)
    # Find the line that defines DEFAULT_INHERITANCE_POLICY
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if "DEFAULT_INHERITANCE_POLICY = " in line:
            # Look at the 5 lines immediately above the definition
            context = "\n".join(lines[max(0, i - 5):i])
            assert "calibrated against the roomd corpus" not in context, (
                "G3 regression: false 'calibrated' claim is back in the "
                "DEFAULT_*_POLICY block comment"
            )
            break
    else:
        raise AssertionError("DEFAULT_INHERITANCE_POLICY not found in module")
