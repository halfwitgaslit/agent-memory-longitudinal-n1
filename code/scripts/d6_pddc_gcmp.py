#!/usr/bin/env python3
"""Deliverable 6 — PDDC + GCMP on real-shaped data.

PDDC test:
  - Generate ~100 synthetic trajectories with KNOWN signal-mix parameters
  - Fit PDDC against the trajectories
  - Verify:
    a) fitted loss < baseline (default-params) loss (PDDC strictly improves)
    b) signal-mix weights move in the right direction (sign-match with truth)
    c) out-of-sample (held-out) prediction beats default FSRS-6

GCMP test:
  - Build a worktree-parent-child structure (1 parent, 2 children)
  - Write 5 memories in the child with varied signal profiles
  - Verify the InheritancePolicy + PromotionPolicy correctly classify
    them per pre-registered defaults (architecture/v1.md §4.4)

Evidence: phd/decisions/loop2_evidence/d6_pddc_gcmp_report.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT.parent / "decisions" / "loop2_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
REPORT = EVIDENCE_DIR / "d6_pddc_gcmp_report.json"


def part_a_pddc() -> dict:
    """Test PDDC fit on synthetic trajectories from known params."""
    from calibration.decay import (
        PDDCalibrator,
        PDDC_DEFAULT_PARAMS_22,
        generate_synthetic_trajectories,
        pddc_loss,
    )

    # Define a "ground truth" parameter vector that DIFFERS from defaults.
    # Specifically perturb the 5 PDDC signal-mix params (indices 21..25):
    #   defaults: (w_hit=2.0, w_support=0.5, w_conflict=-1.0, w_task=1.5, b=0)
    #   truth:    (w_hit=3.5, w_support=1.2, w_conflict=-2.5, w_task=2.8, b=0.4)
    true_params = PDDC_DEFAULT_PARAMS_22.copy()
    true_params[21] = 3.5    # w_hit
    true_params[22] = 1.2    # w_support
    true_params[23] = -2.5   # w_conflict
    true_params[24] = 2.8    # w_task_delta
    true_params[25] = 0.4    # bias

    # Generate train/eval split: 80 train memories, 20 held-out, 10 reviews each
    train_traj = generate_synthetic_trajectories(
        true_params=true_params, n_memories=80, n_reviews_per_memory=10, seed=42,
    )
    eval_traj = generate_synthetic_trajectories(
        true_params=true_params, n_memories=20, n_reviews_per_memory=10, seed=99,
    )

    print(f"  PDDC train trajectories: {len(train_traj)}, eval: {len(eval_traj)}")
    print(f"  total train observations: {sum(len(t) for t in train_traj)}")

    cal = PDDCalibrator()
    baseline_train_loss = pddc_loss(PDDC_DEFAULT_PARAMS_22, train_traj)
    baseline_eval_loss = pddc_loss(PDDC_DEFAULT_PARAMS_22, eval_traj)
    print(f"  baseline (default params) train loss: {baseline_train_loss:.5f}")
    print(f"  baseline (default params) eval  loss: {baseline_eval_loss:.5f}")

    # Fit on train
    t0 = time.time()
    fit_info = cal.fit(train_traj, max_iter=200)
    elapsed = time.time() - t0
    print(f"  fit elapsed: {elapsed:.2f}s")
    print(f"  fit info: {fit_info}")

    fitted_train_loss = pddc_loss(cal.params, train_traj)
    fitted_eval_loss = pddc_loss(cal.params, eval_traj)
    print(f"  fitted train loss: {fitted_train_loss:.5f} (Δ={baseline_train_loss-fitted_train_loss:+.5f})")
    print(f"  fitted eval  loss: {fitted_eval_loss:.5f} (Δ={baseline_eval_loss-fitted_eval_loss:+.5f})")

    # Sign-match: do the fitted signal-mix params move in the right direction
    # relative to defaults, toward the truth?
    default_smix = PDDC_DEFAULT_PARAMS_22[21:26]
    true_smix = true_params[21:26]
    fitted_smix = cal.params[21:26]
    signs_true = np.sign(true_smix - default_smix)
    signs_fitted = np.sign(fitted_smix - default_smix)
    sign_matches = int(np.sum(signs_true == signs_fitted))

    print(f"  signal-mix defaults: {default_smix}")
    print(f"  signal-mix truth:    {true_smix}")
    print(f"  signal-mix fitted:   {fitted_smix}")
    print(f"  sign-match: {sign_matches}/5")

    return {
        "n_train_memories": len(train_traj),
        "n_eval_memories": len(eval_traj),
        "true_params_signal_mix": true_smix.tolist(),
        "default_params_signal_mix": default_smix.tolist(),
        "fitted_params_signal_mix": fitted_smix.tolist(),
        "baseline_train_loss": float(baseline_train_loss),
        "baseline_eval_loss": float(baseline_eval_loss),
        "fitted_train_loss": float(fitted_train_loss),
        "fitted_eval_loss": float(fitted_eval_loss),
        "train_loss_reduction": float(baseline_train_loss - fitted_train_loss),
        "eval_loss_reduction": float(baseline_eval_loss - fitted_eval_loss),
        "sign_match_count_of_5": sign_matches,
        "fit_elapsed_s": elapsed,
        "fit_info": fit_info,
        "PASS_strict_improve_train": fitted_train_loss < baseline_train_loss,
        "PASS_strict_improve_eval":  fitted_eval_loss  < baseline_eval_loss,
        "PASS_sign_match_majority": sign_matches >= 3,
    }


def part_b_gcmp() -> dict:
    """Test GCMP policy on a parent-child worktree fleet."""
    from governance.cross_worktree import (
        ForkContext,
        GCMPManager,
        InheritancePolicy,
        PromotionPolicy,
        DEFAULT_INHERITANCE_POLICY,
        DEFAULT_PROMOTION_POLICY,
        WorktreeMemoryView,
    )
    from memory.base import Memory
    from memory.null_backend import NullBackend

    # Use a simple NullBackend wrapped with a WorktreeMemoryView so we can
    # construct Memory objects directly without going through an LLM-backed
    # extractor.
    backend = NullBackend(scope={"user_id": "vector", "project": "roomd"})
    parent = WorktreeMemoryView(
        backend=backend,
        worktree_id="main",
        parent_branch=None,
        user_id="vector",
        project="roomd",
    )
    child = WorktreeMemoryView(
        backend=backend,
        worktree_id="fix/zod-drift",
        parent_branch="main",
        user_id="vector",
        project="roomd",
    )

    mgr = GCMPManager(
        backend=backend,
        inheritance_policy=DEFAULT_INHERITANCE_POLICY,
        promotion_policy=DEFAULT_PROMOTION_POLICY,
    )
    mgr.register_worktree("main", parent_branch="")
    mgr.register_worktree("fix/zod-drift", parent_branch="main")

    # Construct 5 child-worktree memories with varied profiles.
    # Memory has fields: support_count, hit_count, conflict_count, metadata.
    # PromotionPolicy.is_eligible checks:
    #   support_count >= 3, hit_rate >= 0.7, conflict <= 1, task_delta >= 0.05
    test_memories = [
        # m0: durable convention (should promote) — high support, high hit_rate, no conflicts, positive task delta
        Memory(memory_id="m0", text="In roomd we use Pydantic v2 for all schemas",
               support_count=5, hit_count=12, conflict_count=0,
               metadata={"tags": ["convention"], "task_success_delta": 0.18}),
        # m1: low support (should NOT promote)
        Memory(memory_id="m1", text="The user prefers terse output",
               support_count=1, hit_count=2, conflict_count=0,
               metadata={"task_success_delta": 0.10}),
        # m2: too many conflicts (should NOT promote)
        Memory(memory_id="m2", text="We deprecated the old auth module",
               support_count=4, hit_count=8, conflict_count=3,
               metadata={"task_success_delta": 0.12}),
        # m3: task_success_delta below threshold (should NOT promote)
        Memory(memory_id="m3", text="Logging uses structlog v23+",
               support_count=3, hit_count=7, conflict_count=0,
               metadata={"task_success_delta": 0.01}),
        # m4: durable schema (should promote)
        Memory(memory_id="m4", text="DB schema migrations live in alembic/versions/",
               support_count=6, hit_count=14, conflict_count=1,
               metadata={"tags": ["schema"], "task_success_delta": 0.22}),
    ]

    # Test PromotionPolicy.is_eligible on each
    promotion_decisions = {}
    for m in test_memories:
        eligible = mgr.promotion_policy.is_eligible(m)
        promotion_decisions[m.memory_id] = {
            "text": m.text,
            "support": m.support_count,
            "hits": m.hit_count,
            "conflicts": m.conflict_count,
            "task_delta": float(m.metadata.get("task_success_delta", 0.0)),
            "tags": m.metadata.get("tags"),
            "eligible_for_promotion": eligible,
        }
        print(f"  {m.memory_id}: support={m.support_count} hits={m.hit_count} "
              f"conflicts={m.conflict_count} task_delta={m.metadata.get('task_success_delta')} "
              f"→ eligible={eligible}")

    # Expected per the pre-registered defaults:
    expected = {"m0": True, "m1": False, "m2": False, "m3": False, "m4": True}
    actual = {mid: d["eligible_for_promotion"] for mid, d in promotion_decisions.items()}
    matches = sum(1 for k in expected if expected[k] == actual[k])

    # Test InheritancePolicy: which child memories should propagate to a NEW child fork?
    fork_ctx = ForkContext(
        parent_worktree="fix/zod-drift",
        child_worktree="fix/zod-drift-attempt-2",
        fork_ts_utc=time.time(),
        user_id="vector",
        project="roomd",
    )
    inherited = mgr.inheritance_policy.apply(test_memories, fork_ctx)
    inherited_ids = [m.memory_id for m in inherited]
    print(f"  fork inheritance: {inherited_ids}")

    # Expected inheritance per default predicate (durable tag or support_count >= 3):
    #   m0: tag="convention" → inherit
    #   m1: support=1, no tag → SKIP
    #   m2: support=4, no tag → inherit (high support fallback)
    #   m3: support=3, no tag → inherit
    #   m4: tag="schema" → inherit
    expected_inherit = ["m0", "m2", "m3", "m4"]
    inherit_match = set(inherited_ids) == set(expected_inherit)

    return {
        "promotion_decisions": promotion_decisions,
        "promotion_expected": expected,
        "promotion_actual": actual,
        "promotion_correct_count": matches,
        "promotion_total": len(expected),
        "inherited_ids": inherited_ids,
        "inherited_expected": expected_inherit,
        "inheritance_match": inherit_match,
        "PASS_promotion_all_correct": matches == len(expected),
        "PASS_inheritance_correct": inherit_match,
    }


def main() -> int:
    report: dict = {"started_utc": time.time()}

    print("=== Part A: PDDC ===")
    a = part_a_pddc()
    report["part_a_pddc"] = a

    print("\n=== Part B: GCMP ===")
    b = part_b_gcmp()
    report["part_b_gcmp"] = b

    # Aggregate pass/fail
    failures: list = []
    if not a["PASS_strict_improve_train"]:
        failures.append("PDDC train loss did not improve over baseline")
    if not a["PASS_strict_improve_eval"]:
        failures.append("PDDC eval loss did not improve over baseline")
    if not a["PASS_sign_match_majority"]:
        failures.append(f"PDDC sign-match {a['sign_match_count_of_5']}/5 < 3")
    if not b["PASS_promotion_all_correct"]:
        failures.append(f"GCMP promotion {b['promotion_correct_count']}/{b['promotion_total']} incorrect")
    if not b["PASS_inheritance_correct"]:
        failures.append("GCMP inheritance set mismatch")

    report["failures"] = failures
    report["status"] = "PASS" if not failures else "FAIL"
    report["ended_utc"] = time.time()
    REPORT.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nReport: {REPORT}")
    print(f"Status: {report['status']}")
    for f in failures:
        print(f"  FAIL: {f}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
