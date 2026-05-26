# N3 — Per-project Rule-Lifecycle FSM with Empirically Calibrated Decay
## Opus Consolidated Verdict

**Date:** 2026-05-25T22:00:00Z
**Consolidator:** Opus 4.7
**Lanes consolidated:** Sonnet A (academic) · Sonnet B (industry/OSS) · Sonnet C (adjacent fields)

---

## 1. Final verdict

**`partial-overlap`** — the conjunction survives *only* if reframed as a domain-transfer / substrate-novelty contribution. The original framing ("FSM + empirically calibrated decay") is **dead** as a methodological novelty in its constituent parts.

## 2. Confidence

**HIGH.** All three lanes converged independently. Lane A (academic) initially returned "survived strong"; Lane C (adjacent) materially weakened it by surfacing FSRS (2022) and ISO 15489 — both of which the academic lane missed because they sit outside the ML/NLP venue radius. Lane B confirmed the OSS landscape is greenfield for the conjunction but cannot rescue the methodological claim. The combination of FSRS + Koren temporal CF + ISO 15489 + MACLA forms an independently-corroborated kill ring around the *general* claim. The only undefeated angle is *substrate*.

## 3. Top 3 closest prior works

### #1 — FSRS / FSRS-6 (Free Spaced Repetition Scheduler, 2022–2024, Anki)
**Similarity quote (C-lane):** *"FSRS-6 has 21 trainable parameters fitted via gradient descent (log-loss/binary cross-entropy) against real user review history… per-user calibration… personalized decay exponent w20 fitted from review history."*
**What it did NOT do:** No FSM with named semantic-content states (draft/active/deprecated/archived) — scheduler states (new/learning/review/suspended/buried) are queue positions, not lifecycle. Calibration signal is binary human recall, not multi-dimensional agent utility. Substrate is flashcard, not named rule record consumed by an agent. **Owns the "empirically calibrated decay" sub-claim outright.**

### #2 — ISO 15489-1:2016 Records Management
**Similarity quote (C-lane):** *"Defines record lifecycle FSM (create, capture, manage, dispose). Transitions are policy-driven by fixed time windows / legal requirements."*
**What it did NOT do:** Transitions are fixed-policy and human-driven, not calibrated from any empirical usage signal. No decay function. **Owns the "lifecycle FSM for records" sub-claim outright.** MDM systems (candidate → golden → retired) reinforce this — same FSM pattern, also non-calibrated.

### #3 — MACLA (arxiv 2512.18950) — closest in-domain analogue
**Similarity quote (A-lane):** *"Bayesian reliability posteriors to drive pruning… parameters (λr=0.5, λf=0.3, λt=0.2) were set by grid search on a validation set."*
**What it did NOT do:** Grid search on a held-out benchmark ≠ calibration from real deployment traces. Two implicit states (active/pruned), not a 4-state FSM. Signal is benchmark accuracy, not agent task success in deployment. **The closest academic-agent-memory neighbor — the contribution must differentiate from MACLA on (a) deployment-trace calibration vs benchmark grid search, and (b) named multi-state FSM vs continuous score with single threshold.**

Honorable mentions that contribute to the kill: Koren 2010 temporal CF (decay calibration via gradient descent on rating data — owns the technique in RecSys), FadeMem and SSGM (decay math published, no calibration), Library Drift/Ratchet (evidence-gated retirement, no calibrated thresholds), ByteRover AKL (maturity tiers, no confirmed FSM or calibration), ARC (online self-tuning, no FSM, no rules).

## 4. The exact surviving gap

**Sub-claim-by-sub-claim adjudication:**

| Sub-claim | Status | Killed by |
|---|---|---|
| "Calibrating decay parameters from real usage data is novel" | **DEAD** | FSRS (since 2022, per-user gradient descent on 700M reviews), Koren 2010 (gradient descent on rating data), ARC (online p-tuning) |
| "Lifecycle FSM with named states (draft/active/deprecated/archived) is novel" | **DEAD** | ISO 15489, MDM, OWL versioning, production-rules engines (Drools enable/disable/version) — all have staged FSMs |
| "Applied to LLM agent rule memory" | **SURVIVES** — substrate is genuinely new. No surveyed agent-memory system (mem0, Letta, Hindsight, A-Mem, Cognee, Mastra, ByteRover, EverMemOS, MACLA, FadeMem, SSGM) implements the conjunction |
| "Using agent-task-success as the calibration signal" | **SURVIVES** — FSRS uses recall outcomes; Koren uses rating loss; ARC uses hit-rate; none use multi-dimensional agent utility (support_count + conflict events + hit-rate + task-success delta) |
| "Per-project (n=1 deployment-trace) calibration vs benchmark grid search" | **SURVIVES (narrowly)** — MACLA grid-searches on a held-out benchmark; no agent-memory work calibrates on real per-deployment session traces |

**The single sentence that survives:** *"A 4-state FSM (draft → active → deprecated → archived) for individual agent rule records, with transition thresholds and decay rates fitted via gradient descent (or equivalent) against multi-dimensional deployment-session signals (support_count, hit-rate, conflict-detection events, agent task-success delta) collected from a single project's actual usage."* The novelty here is **substrate + signal**, not method.

## 5. Repositioning recommendation

**Use exactly the C-lane reframe — it is the only defensible position against a hostile reviewer:**

> *"We adapt SRS-style empirically-calibrated decay (cf. FSRS) and records-management-style lifecycle FSM (cf. ISO 15489) to the novel substrate of LLM agent rule memory, with agent task-success as the calibration signal."*

**Reinforcement to make it survive senior-reviewer pressure:**
1. **Lead with the substrate-and-signal claim**, not the method claim. Anyone who reads "empirically calibrated decay" first will reach for FSRS in their head before they finish the sentence. Lead with "agent rule memory with deployment-calibrated lifecycle."
2. **Cite FSRS, Koren 2010, and ISO 15489 explicitly in the related-work paragraph and own the adaptation framing.** Pretending these don't exist is the fastest path to desk-reject.
3. **Differentiate from MACLA in the methods section** on three axes: (i) per-deployment trace vs benchmark grid search; (ii) 4-state FSM vs binary active/pruned; (iii) multi-signal calibration (4 dimensions) vs 3-weight grid search.
4. **The empirical contribution carries weight that the methodological contribution cannot.** If you can show that *per-project calibration* beats *FSRS-default-parameters-transferred-to-agent-rules* on real agent task outcomes, that is a paper. The FSM itself is bookkeeping.

## 6. Falsification-test residual risk

**Residual risk: MEDIUM.** Specific concerns:

- **ByteRover AKL** internals (arxiv 2604.01599) were not fully extractable by Lane B; the PDF was not parseable. AKL's "maturity tiers + recency decay + importance scoring" is the closest unconfirmed match. A future reviewer with access to the AKL implementation could surface a kill. **Mitigation:** Lane B should re-attempt with a different PDF parser, or contact the authors.
- **MACLA's calibration methodology** was characterized from abstract only; if MACLA's grid search is over deployment-derived held-out data (not synthetic benchmark), the differentiation collapses to "FSM granularity" alone, which is weak.
- **FSRS-as-applied-to-agent-rules** is an obvious follow-up someone could publish first if our deployment data sits unpublished. The clock is ticking.
- **Concept drift detection literature (river/MOA, ADWIN)** was surveyed superficially by C-lane and ruled out, but a deeper dive into adaptive thresholding in data-stream mining could surface a closer analogue.
- **Business rules management systems (Drools "decision tables with audit trails", IBM ODM "rule lifecycle states")** were ruled out by C-lane, but enterprise BRMS documentation is hard to fully canvas; some proprietary BRMS may already have empirically-calibrated rule retirement.

## 7. Per-researcher lane verdicts

| Lane | Standalone verdict | Confidence |
|---|---|---|
| **A (academic)** | "SURVIVED (strong)" — no ML/NLP paper combines named FSM + deployment-calibrated decay | HIGH within ML/NLP |
| **B (industry/OSS)** | "SURVIVED (high confidence)" — greenfield in mem0/Letta/Hindsight/etc. landscape | HIGH within OSS agent-memory |
| **C (adjacent fields)** | "PARTIAL-OVERLAP" — FSRS owns calibration, ISO 15489 owns FSM, conjunction is the gap | MEDIUM-HIGH |

**Disagreement resolution:** Lanes A and B searched within "agent memory" — a young field where greenfield is easy. Lane C correctly looked across mature fields where these problems are *solved*. **Lane C is right and must override.** Verdicts A and B are correct for their domains but methodologically incomplete: they did not falsify the *technique*, only the *combination-in-this-substrate*. The audit's job is to falsify novelty *broadly*, not just within one venue. Therefore the consolidated verdict adopts Lane C's framing: `partial-overlap`, with the surviving gap being substrate-plus-signal, not method.

## 8. Reviewer-grade summary (≤150 words)

This is a domain-transfer contribution masquerading as a methodological one. FSRS (2022+) calibrates per-user forgetting parameters from real review traces via gradient descent — the "empirical decay calibration" sub-claim is **owned in cognitive psychology and shipped to millions of Anki users**. ISO 15489 and MDM systems have defined staged record lifecycles for decades — the "lifecycle FSM" sub-claim is **owned in records management**. MACLA (2512.18950) already brings calibrated multi-factor utility to agent memory, albeit via benchmark grid-search. The conjunction "FSM + calibrated decay" is therefore neither novel as method nor novel as integration. What *does* survive is narrow: applying both, jointly, to LLM agent rule memory with a multi-dimensional deployment-signal (support_count + conflict events + hit-rate + task-success delta) rather than recall/rating loss. The authors must lead with substrate-and-signal novelty, cite FSRS, Koren, MACLA, ISO 15489 in related work, and differentiate from MACLA on calibration-source (deployment trace vs benchmark). Empirical results — not architecture — are the only path to acceptance.
