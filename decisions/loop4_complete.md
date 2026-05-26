# Loop 4 — Complete

**Date:** 2026-05-26
**Owner:** Vector (stephengduke@gmail.com)
**Priority commit:** `4c913cd` (unchanged)
**Pre-registration hash:** `14645d41cc73fe32f82d8ac4ba9b6aa0940750be244d0473a3f29553b21b6fea`
(re-verified 2026-05-26; `preregistration/v1.md` + `code/eval/experimental_constants.py` byte-for-byte unchanged)

## Mandate

> Close all 12 gaps from `decisions/loop3_evidence/GAP_REGISTER.md`
> to "100% complete, no skipping."

## Outcome: all 12 gaps fixed

| Gap | Title | Status | Evidence file |
|-----|-------|--------|---------------|
| G1 | Skill never auto-fires | FIXED | [g1_hook_auto_fire.md](loop4_evidence/g1_hook_auto_fire.md) |
| G2 | PDDC on synthetic, not real data | FIXED (H2 deferred to Phase 2) | [g2_pddc_real_data.md](loop4_evidence/g2_pddc_real_data.md) |
| G3 | GCMP denominator + fork_worktree + calibration claim | FIXED | [g3_gcmp_fixes.md](loop4_evidence/g3_gcmp_fixes.md) |
| G4 | Letta silently fails while reporting healthy=True | FIXED (substrate-limited) | [g4_letta_honest_mem.md](loop4_evidence/g4_letta_honest_mem.md) |
| G5 | Hindsight writes counters but no data | FIXED (substrate-limited) | [g5_hindsight_honest_mem.md](loop4_evidence/g5_hindsight_honest_mem.md) |
| G6 | Cognee no API-key fallback | FIXED (per gap's "document and skip" alt) | [g6_cognee_honest_mem.md](loop4_evidence/g6_cognee_honest_mem.md) |
| G7 | Mem0 cross-process lock blocks | FIXED | [g7_subprocess_isolation.md](loop4_evidence/g7_subprocess_isolation.md) |
| G8 | D2/D5 unreproducible idempotent skips | FIXED | [g8_d2_d5_fresh_capture.md](loop4_evidence/g8_d2_d5_fresh_capture.md) |
| G9 | -1 sentinel leaks in D5 | FIXED | [g9_sentinel_eliminated.md](loop4_evidence/g9_sentinel_eliminated.md) |
| G10 | CLI attribution lost in bridge mode | FIXED | [g10_cli_attribution.md](loop4_evidence/g10_cli_attribution.md) |
| G11 | Skill user_id mismatch | FIXED | [g11_user_id_canonical.md](loop4_evidence/g11_user_id_canonical.md) |
| G12 | Pre-reg drift on Mem0 LLM path | FIXED via amendment | [v1_amendment_001.md](../preregistration/v1_amendment_001.md) |

## What "FIXED (substrate-limited)" means

G4 (Letta) and G5 (Hindsight) and G6 (Cognee) were originally written
because the backends were silently lying. The Loop 4 fix is:

1. The HONEST-Mem invariants are restored: any failure surfaces as
   `healthy=False`, `n_errors > 0`, `last_error` populated.
2. The synthetic-ID hack (Hindsight) is gone — `add()` returns real
   memory_unit_ids from `retain_async` or returns `[]`.
3. The hardcoded model handle (Letta) is replaced with runtime
   discovery from the live server.
4. Mem0's `_safe_count_memories` no longer returns `-1` (G9).
5. Mem0 metadata round-trips `_origin_cli` (G10).

The remaining "substrate" issue is that the EMBEDDED LLM/embedding
endpoints these substrates rely on (inference.letta.com for Letta;
real ANTHROPIC API for Hindsight + Cognee) are unreachable from this
offline env without an API key. When that's the case, the backends
DEGRADE HONESTLY rather than silently returning empty results while
reporting healthy=True. That's exactly what `architecture/v1.md` §4.2
calls "SKIPPED-UNHEALTHY" — the documented degradation strategy.

Phase 2 deployment with a real ANTHROPIC_API_KEY (or paid
inference.letta.com account) will resolve these substrate dependencies.

## Pytest

- **Baseline** (pre-Loop-4): 77 passed
- **Loop 4 final**: 82 passed (+5)
  - G3 governance regression guards: 3 new
  - G9 sentinel regression guards: 2 new
- No regressions. Hash unchanged.

## Commits pushed to `github.com:halfwitgaslit/agent-memory-longitudinal-n1`

```
32a71f8  [Gap G1+G11+G12] auto-fire UserPromptSubmit hook + canonical user_id + LLM-path amendment
b8c39ed  [Gap G7+G9+G10] subprocess isolation, sentinel elimination, CLI attribution
2f73a47  [Gap G4+G5+G6] HONEST-Mem invariants restored across Letta/Hindsight/Cognee
774b2cd  [Gap G2+G3+G8] PDDC on real data, GCMP bug fixes, D2/D5 fresh capture
```

All four commits push cleanly to `origin/main`.

## What's NOT claimed

This Loop 4 does NOT claim:

1. **H2 (PDDC > FSRS-defaults) settled.** The G2 fix runs PDDC on REAL
   roomd compaction data and the naive H2 numerical test passes (66.8%
   eval improvement). But the report and verdict.json explicitly flag
   `signal_degeneracy_warning: true` — hit-rate variance is 0.0085.
   Publication-grade H2 evidence requires actual usage-trace signals,
   which is what the pre-registered Phase 2 design captures.
2. **All backends ingest end-to-end without an API key.** Letta /
   Hindsight / Cognee need a real LLM/embedding endpoint. Loop 4
   restored HONEST-Mem invariants on the failure path; the substrate
   dependency is documented in each backend's evidence file.
3. **GCMP thresholds calibrated.** The G3 fix removes the
   "calibrated against the roomd corpus" false claim. The defaults are
   honest hand-tuned values; Phase 2 will calibrate against real
   promotion-event logs.

## What IS claimed (publication-quality)

1. **The injection pipeline works end-to-end.** G1 evidence shows a real
   `claude -p` session retrieves a seeded sentinel verbatim — the first
   independent demonstration in the project that the model's output
   reflects content from the memory backend, with no skill prompting.
2. **HONEST-Mem invariants hold across all 6 arms.** Whether each arm
   succeeds at ingest depends on substrate availability, but failures
   are loud, not silent.
3. **Cross-CLI bridging preserves attribution.** G10 shows `_origin_cli`
   round-trips through the bridge-scope mode.
4. **Pre-reg priority unchanged.** Hash `14645d4...` verifies; commit
   `4c913cd` remains the priority anchor.
5. **The Mem0 cross-process qdrant lock is resolved.** Two concurrent
   processes successfully add+search; Phase 2 parallel-arm execution is
   unblocked.

## Spend

Total Loop 4 API spend: ~$5 estimated (4 `claude -p` calls for G1 e2e
test at <$1 each; PDDC + GCMP + tests are all local compute with no
API calls; D2/D5 fresh runs incurred ~$0.11 via subscription billing as
captured in cli_meter; Mem0SubprocessBackend verification used local
compute only).

Far under the $400 cap.

## Owner attention needed

None blocking. Phase 2 deployment decisions:
- Provide a real `ANTHROPIC_API_KEY` to fully exercise Hindsight + Cognee
  in production, OR accept those arms as SKIPPED-UNHEALTHY under the
  current operational degradation policy.
- Decide whether to implement a Cognee LiteLLM custom provider routing
  to `claude -p` (deferred in Loop 4 — Mem0 amendment + Cognee
  "requires-real-key" documentation is sufficient per gap text).

## Resumability

`decisions/loop4_state.json` is the structured resumable state. Each gap
records `status`, `evidence`, `key_artifact`, optional `note`, and `commit`.
The next loop (if any) can read this directly.
