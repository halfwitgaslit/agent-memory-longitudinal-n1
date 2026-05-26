# N3 Novelty Audit — Academic Falsification
**Auditor:** Sonnet A (academic lane)
**Date:** 2026-05-25T22:00:00Z
**Claim:** Per-project rule-lifecycle FSM (draft→active→deprecated→archived) with decay parameters CALIBRATED from real session data.

---

## Iteration 1: Broad survey sweep

**Papers checked:**
- AMV-L (2603.04443): Uses "lifecycle tiers" with promotion/demotion/eviction, but abstract reveals no named FSM states and no empirical calibration of decay — it's a latency-optimization system, not a rule governance system.
- Library Drift / Ratchet (2605.19576): Outcome-driven retirement + bounded active-cap + per-skill contribution scores. No named FSM states. No empirical calibration of retirement thresholds — evidence-gated but threshold is not learned from deployment data.
- MACLA (2512.18950): Uses Bayesian reliability posteriors to drive pruning. **Partial match on calibration**: parameters (λr=0.5, λf=0.3, λt=0.2) were set by grid search on a validation set — this is closer to empirical calibration than pure theory, but (a) it's a grid search on held-out benchmark data, not real deployment sessions, and (b) no named FSM with draft/deprecated/archived states.
- FadeMem (2601.18642): Exponential decay formula with semantic relevance, access frequency, temporal patterns. Biologically-inspired (Ebbinghaus), **not calibrated from deployment data**. No explicit FSM.
- EverMemOS (2601.02163): Episodic→Semantic consolidation pipeline. Brain-inspired stages (MemCell→MemScene). Not a formal FSM; stages are pipeline phases, not lifecycle states for individual records. No calibrated decay.
- CraniMem (2603.15642): Importance weighting + temporal decay. No FSM. No empirical calibration evidence found.

---

## Iteration 2: Governance and lifecycle-specific systems

**Papers checked:**
- StageMem (2604.16774): Three stages — transient, working, durable. Closest to a named stage hierarchy. Transitions driven by **capacity pressure**, not usage signals. Authors **explicitly state thresholds are hand-chosen**, not data-driven. Does not falsify.
- SSGM (2603.11768): Weibull decay function for temporal relevance. Parameters (η, κ) are **design choices, not empirically calibrated**. No FSM with named states. Governance is continuous filtering, not discrete state transitions. Does not falsify.
- MemoryBank: Ebbinghaus forgetting curve — theoretical, not calibrated from deployment data.
- Knowledge editing literature (MEND, ROME, MEMIT, GRACE): These edit model weights, not external memory records. No lifecycle FSM for rule records. No empirical decay calibration relevant to the claim.

---

## Iteration 3: Adjacent domains

**Production rule systems (CLIPS, Drools, OPS5):** Rule lifecycle in production-rule engines is managed by working-memory activation/retraction cycles, not a named FSM with deprecated/archived states. No empirical decay calibration. Not a match.

**Database TTL/tombstoning (Cassandra, ScyllaDB, LSM compaction):** TTL is a single scalar, not a multi-state FSM. Parameters are hand-configured by operators, not auto-calibrated from access patterns. Not a match.

**Knowledge editing maintenance (Selective Knowledge Suppression, Distributed Multi-Layer Editing):** Focus is on correcting factual errors in model weights, not managing external rule records through lifecycle states. No FSM, no calibrated decay.

**ITS/expert-system maintenance:** Literature addresses knowledge acquisition and validation but not empirically calibrated decay FSMs for rule records.

---

## Key distinctions established

| System | Named FSM states | Empirically calibrated decay |
|---|---|---|
| FadeMem | No | No (theory-based) |
| MACLA | No (implicit active/pruned only) | Partial (grid search on benchmark, not deployment data) |
| Library Drift / Ratchet | No | No (evidence-gated but threshold not learned) |
| StageMem | No (3 pipeline stages, not per-record FSM) | No (explicitly hand-chosen) |
| SSGM | No | No (Weibull params are design choices) |
| AMV-L | No (tiers, not FSM) | Unknown; latency-focused not rule-governance |
| EverMemOS | No | No (neuroscience-inspired) |
| CraniMem | No | No |

**MACLA is the strongest analogue:** Bayesian reliability posteriors + multi-factor utility score (reliability, frequency, recency) with weights calibrated by grid search. But this is (a) benchmark grid search, not deployment session data, and (b) two implicit states only (active, pruned), not a full 4-state FSM.

---

## Verdict

**SURVIVED (strong)**

No system in the academic literature combines BOTH:
1. An explicit FSM with multiple named lifecycle states for individual rule/memory records (draft → active → deprecated → archived or equivalent)
2. Decay parameters calibrated from real deployment/session data rather than theory, hand-tuning, or benchmark grid search

**Strongest analogue requiring differentiation:** MACLA (2512.18950) — empirically tuned multi-factor utility with Bayesian reliability tracking. The N3 claim must differentiate on: (a) per-project calibration from actual session traces vs. benchmark grid search, and (b) explicit multi-state FSM vs. a continuous score with a single pruning threshold.

**Second closest:** Library Drift / Ratchet — evidence-gated retirement is thematically close, but the retirement logic is rule-based and threshold-free (LLM decides), not a calibrated FSM.
