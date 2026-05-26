# Researcher C — Devil's Advocate Pass — N3
**Date:** 2026-05-25

## Did I miss anything that could kill N3?

1. **FSRS is the strongest kill candidate.** FSRS-6 calibrates 21 parameters per user from real review data using gradient descent. If someone argues "calibrating decay from usage data is the claim," FSRS pre-empts it entirely (since 2022). The counter-argument that saves N3: FSRS's decay signal is binary human recall (correct/incorrect), whereas N3's signal is multi-dimensional agent utility (support_count, conflict events, task-success delta). Different domain, different signal, different substrate (flashcard vs. named rule record). The FSM is also absent in FSRS.

2. **Koren 2010 temporal CF is the second kill candidate.** It fits exponential decay parameters from real rating data via gradient descent. Pre-empts "calibrating decay from data." Saved by same argument: operates on user preference weights in a matrix, not on named discrete rule records with lifecycle states.

3. **What about Drools / production rules engines?** Drools and RETE-based engines have rule activation history (salience, agenda), but no automated deprecation. Calibration is zero — all policy is human-authored.

4. **What about ARC (Adaptive Replacement Cache)?** ARC self-tunes its partition parameter p online, making it a form of empirical calibration. But it's binary (in/out), single-parameter, no FSM, operates on cache lines not named rules.

5. **Most dangerous blind spot:** Session-based recommendation systems (GRU4Rec, SASRec, BERT4Rec) model temporal decay of user interest within a session, and some use empirically fitted decay rates. But again: these operate on item-interaction sequences, not named rule records in an agent memory store.

6. **Concept drift detection (ADWIN, DDM):** Monitors statistical shift in a data stream and triggers model refresh. Structurally adjacent (usage-based staleness detection). Not a kill: concept drift detects change in a *model*'s performance, not retirement of individual *named rules* through a staged FSM.

## Confidence assessment

Search exhaustiveness: MEDIUM-HIGH. I covered cognitive psychology (FSRS, SuperMemo), IR (BM25-temporal, TempRetriever), caching (ARC, Redis LFU), RecSys (Koren), RL (PER), ontology (OWL versioning), records management (ISO 15489), agent memory (SSGM, FadeMem). I did not do deep dives into: (a) Drools/business rules management systems, (b) concept drift in data stream mining (river/MOA), (c) active learning budget allocation. None of these are likely to produce a clean kill, but they could surface partial overlap.

## Final verdict: PARTIAL-OVERLAP

- The "empirically calibrated decay" sub-claim is pre-empted by FSRS (and Koren CF) in adjacent domains.
- The "lifecycle FSM" sub-claim is pre-empted by ISO 15489 / MDM in records management domains.
- The *combination* applied to *agent rule records* with *agent task-success signals* is not pre-empted.
- Contribution should be repositioned as: "We apply decay calibration (well-established in SRS) and lifecycle FSM (well-established in records management) to the novel substrate of LLM agent rule memory, using agent deployment outcomes as the calibration signal."
