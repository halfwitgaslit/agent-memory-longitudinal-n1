# Sonnet B — Iteration 3: Final Verdict
Date: 2026-05-25T22:00:00Z
Auditor: Sonnet B (industry/OSS lane)
Claim: N3 — Per-project rule-lifecycle FSM with empirical decay calibration

## Closest Competitors Summary

| System | Named FSM States | Empirical Calibration | Notes |
|---|---|---|---|
| mem0 decay | No (score multiplier) | No (fixed 0.3–1.5× band; auto-tuning roadmap) | Search-time reweighting |
| Letta Blocks | No (storage tiers) | No | Indefinite persistence |
| ByteRover AKL | Unclear (maturity tiers) | No clear evidence | LLM-curated judgment |
| SSGM | No (3 pipeline phases) | No (borrowed Weibull params) | Conceptual only |
| EverMemOS | No (session pipeline) | No | Not per-item |
| A-Mem | No | No | CRUD + semantic linking |
| Hindsight | No | No | 4 memory networks |
| MCP TTL tiers | No (fixed time buckets) | No | Hardcoded 6h/7d/perm |
| Anthropic MCP memory | No | No | Pure CRUD graph |
| LangChain/LlamaIndex | No | No | Session-scoped buffers |
| Cursor | Removed | N/A | Rules files only |
| SSGM Weibull | Theoretical | Not calibrated | Concept paper only |

## Verdict: SURVIVED

**Rationale:**
No system in the OSS/industry landscape implements BOTH requirements of N3:
(a) An explicit FSM with formally named states for individual rule/memory items
(b) Empirical calibration of decay parameters from real per-project usage data

The closest systems:
- **ByteRover AKL** — has a notion of maturity tiers and importance-weighted recency decay, but no confirmed named FSM states and no evidence of empirical calibration. Closest partial overlap.
- **SSGM** — references decay math (Weibull) but it is theoretical, not implemented, not calibrated.
- **mem0 decay** — recency reweighting with a fixed band; per-project auto-tuning is explicitly a future roadmap item.

The B2/C3 finding of "greenfield" is confirmed for the specific conjunction: per-project rule lifecycle FSM + empirically calibrated decay. Individual components exist in isolation (tiered storage, recency scoring, theoretical decay models) but the integrated, calibrated FSM does not exist anywhere in the surveyed landscape.

**Confidence: HIGH** (all major OSS frameworks surveyed; gaps are ByteRover internals and EverMemOS full paper — neither shows FSM signals in accessible artifacts).
