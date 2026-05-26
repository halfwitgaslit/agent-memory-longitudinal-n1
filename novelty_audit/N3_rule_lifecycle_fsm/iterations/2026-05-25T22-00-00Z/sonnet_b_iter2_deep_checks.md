# Sonnet B — Iteration 2: Deep Checks on Closest Candidates
Date: 2026-05-25T22:00:00Z

## ByteRover AKL
- PDF not fully parseable; no named FSM states extractable.
- LLM-curated relevance judgment used instead of predetermined decay function.
- Maturity tiers described but no empirical calibration of tier thresholds.
- Verdict: no confirmed FSM, no empirical calibration. Unconfirmed partial overlap at best.

## SSGM (arxiv 2603.11768)
- References Weibull decay w(Δτ) = exp(−(Δτ/η)^κ); parameters borrowed from prior work, not calibrated.
- Three phases (read/write/reconcile) are pipeline stages, not per-item FSM states.
- "Conceptual governance architecture" — no implementation, no empirical data.
- Verdict: theoretical neighbor, not a kill.

## EverMemOS (arxiv 2601.02163)
- Episodic Trace Formation → Semantic Consolidation → Reconstructive Recollection.
- These are document/session-level pipeline stages, not per-rule item lifecycle states.
- No decay calibration mentioned.
- Verdict: pipeline, not per-item FSM.

## Hindsight (vectorize-io)
- Four memory networks: World, Experiences, Opinion, Observation.
- Operations: Retain, Recall, Reflect. No named lifecycle states per memory item.
- No decay calibration mentioned.
- Verdict: no FSM, no decay.

## A-Mem (agiresearch, NeurIPS 2025)
- CRUD operations framed as "dynamic memory organization."
- No named lifecycle states, no decay mechanism in docs.
- Source code not inspected directly but README and docs show no FSM.
- Verdict: no FSM, no decay.

## MCP TTL-tier implementations (doobidoo, alphaonedev)
- 6h / 7d / permanent tiers with usage-extended TTL.
- Hardcoded buckets ≠ FSM. No empirical calibration.
- Verdict: simple TTL, not FSM + calibration.

## Cursor
- Memories feature removed in v2.1.x. Rules files are static, no lifecycle.
- Verdict: irrelevant.

## Mastra-ai
- Multi-tier memory (history/working/semantic/observational). No FSM, no decay.
- Verdict: no FSM, no decay.

## Ebbinghaus curve implementations (miscellaneous)
- Some community implementations use Ebbinghaus curve with fixed decay factors (e.g., 0.995/hour).
- Fixed formula ≠ empirically calibrated per project.
- Verdict: fixed formula, not calibrated FSM.

## Key Distinction Clarified
The claim N3 requires BOTH:
(a) Explicit FSM with named states (e.g., ACTIVE → STALE → ARCHIVED → EXPIRED with triggers)
(b) Empirical calibration of decay from real project data

No system found has both. Some have (b)-like intent (ByteRover, SSGM) without (a).
None have (a) clearly.
