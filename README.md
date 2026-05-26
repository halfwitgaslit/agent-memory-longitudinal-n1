# PhD-grade trajectory

Pivot date: **2026-05-25**. Supersedes the earlier `decisions/opus_plan_v2.md` (HMA-1, halted at 70%) and `decisions/opus_independent_plan.md` (rejected by adversarial review).

## Goal

Build the strongest foundational substrate for an empirically-defensible, PhD-quality contribution in the agent-memory / coding-agent space. Get a first publication-quality artifact accepted at a major venue. Use that as the platform to push genuinely novel follow-ups.

## Operating principles (locked)

1. **No novelty claim without exhaustive verification.** Every claim has to survive a parallel falsification attempt (see `novelty_audit/`).
2. **Build on giants.** Foundation = existing open-source memory systems (Mem0, Letta, Hindsight, Cognee). We adapt, we don't reinvent.
3. **Empirical-first.** No theory without measurement on real data (Vector's 678-session roomd corpus across Claude Code + Codex).
4. **PhD-grade methodology throughout.** Pre-registration, multi-model, multi-judge, N_runs ≥ 5, MADCovar, Wilcoxon + Bonferroni, bootstrap CI, ablation, negative controls, datasheet, model card, independent replication.
5. **Bold but honest.** Single-subject n=1 longitudinal is a known design — embrace its limits explicitly, don't fake N.

## Layout

| Path | Purpose |
|---|---|
| `README.md` | This file |
| `novelty_audit/` | Phase 0 — falsification of candidate novelty claims (N1-N4) |
| `architecture/` | Phase 1 — foundation substrate design (adapters, memory backend, injection, eval, provenance, lifecycle) |
| `protocols/` | Pre-registered experimental protocols |
| `preregistration/` | Hashed pre-registration commits + OSF entries |
| `reproductions/` | Outside-lab replication packages and results |

## Phases (no phase starts until the previous returns)

- **Phase 0 (1-2 days):** falsify N1-N4 → pick contribution
- **Phase 1 (5-10 days):** build the foundational substrate
- **Phase 2 (4-6 weeks):** longitudinal deployment + measurement
- **Phase 3 (1-2 weeks):** novel layer (depends on Phase 0 verdict)
- **Phase 4 (2-3 weeks):** write, replicate, submit

## Cost posture

Token spend approved. Compute cost: target $0 for the foundation (Mem0/Letta self-hosted on M4 Max). API spend bounded by per-phase pre-registration. Per-phase explicit go required.

## Reuse from HMA-1

The HMA-1 infrastructure is intact and reusable:
- `distillation/code/hma_audit_mini/harness_runner.py` — idempotent JSONL + spend ledger
- Pre-registration mechanics (hash-and-commit-before-eval)
- Bootstrap CI / Wilcoxon / MADCovar code patterns
- The auto-fill-paper pipeline (figs/tables/summary.json → markdown → PDF via weasyprint)
