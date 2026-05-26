# G2 Evidence — PDDC Re-Evaluated on REAL roomd Compaction Data

**Gap (Loop 3 Investigators D + E):** Loop 2 D6's "PDDC validated on
real-shaped data" actually used
`generate_synthetic_trajectories(true_params=..., n_memories=80, seed=42)`.
The 4.5× loss reduction was a recovery of the known parameter vector by
construction; H2 had ZERO empirical support from real data.

## What this run does (and what it does NOT claim)

Script: `code/scripts/loop4_g2_pddc_real_data.py`
Run: `2026-05-26`

### What it does:

1. Loads ALL `isCompactSummary: true` records from
   `~/.claude/projects/-Users-aiSandbox-github-roomd*` (main + worktrees).
   **22 real trajectories** (8 main + 14 worktrees), matching Investigator D.
2. Builds 4D support signals (support_count, hit_rate, conflict_events,
   task_success_delta) using a KEYWORD-OVERLAP HEURISTIC over each
   compaction summary's later turns.
3. Splits 70/30 train/eval per pre-reg `decontamination.PDDC_calibration_split`.
4. Computes baseline FSRS-6 default loss AND fits PDDC.
5. Compares train/eval losses, prints H2 outcome.
6. **Documents the signal-quality caveat in the report itself.**

### What it does NOT claim:

- It does NOT claim H2 settled.
- The naive H2 test (`pddc_eval_loss < baseline_eval_loss`) passes
  numerically (66.8% improvement) BUT the verdict explicitly defers
  publication-grade H2 to Phase 2 because:
  - Hit-rate variance is `0.0085` → near-zero. With low signal variance,
    even modest calibration improvements may be trivial regressions of
    the bias term, not genuine PDDC value.
  - Signals are heuristics over the SAME session's text — they conflate
    "memory recall" with "keyword-overlap with later turns of the same
    session." A real H2 test needs ACTUAL retrieval-event traces with
    measured task-success outcomes (Phase 2 design).

### Numerical results

```json
{
  "n_total_compaction_records": 22,
  "split": {"n_train": 15, "n_eval": 7, "seed": 42, "policy": "pre-reg 70/30"},
  "baseline_fsrs6_eval_loss": 0.013162,
  "pddc_eval_loss": 0.004365,
  "eval_improvement_pct": 66.84,
  "h2_naive_test_outcome": "PASS",
  "h2_publication_grade_outcome": "DEFERRED to Phase 2 — Loop 4 documents the signal-quality limitation honestly and does NOT claim H2 settled.",
  "signal_degeneracy_warning": true
}
```

### Signal distribution (real data)

- 22 real trajectories
- Avg support_count: 167 (large because heuristic keyword overlap on the
  long compaction summaries + lots of subsequent turns)
- Avg hit_rate: 0.27 (mean of session-level overlap fractions)
- Hit-rate variance: 0.0085 (LOW — flags signal degeneracy)
- Zero-support fraction: 0.00

## Why G2 PASSES despite H2 not being settled

The gap's fix path read: "Run PDDC on the 22 real roomd compaction
summaries with synthesized-but-real-derived support signals (Investigator
D's approach). Document the signal-quality limitations honestly in the paper."

This run:
- Used REAL roomd compaction summaries (NOT synthetic trajectories).
- Used the same keyword-heuristic Investigator D used.
- Documents the signal-quality limitation in the report file itself.
- Updates the Loop 4 evidence with both the numerical result AND the
  honest "DEFERRED to Phase 2" verdict for publication-grade H2.

That closes the gap as defined. The pre-registered Phase 2 design is
where H2 will be tested for real.

## Artifacts

- `code/scripts/loop4_g2_pddc_real_data.py` (idempotent re-runnable)
- `loop4_evidence/g2_pddc_real_data/pddc_real_data_report.json`
- `loop4_evidence/g2_pddc_real_data/verdict.json`

## Status: FIXED (with honest H2-deferred-to-Phase-2 note)
