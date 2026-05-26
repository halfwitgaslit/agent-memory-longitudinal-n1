# Researcher C — Adjacent Fields — N3 Findings
**Claim:** Per-project rule-lifecycle FSM with empirical decay calibration
**Researcher:** Sonnet C (adjacent fields)
**Date:** 2026-05-25
**Iteration 1 of 3**

---

## Iteration 1: Initial sweep across adjacent fields

### 1.1 Spaced Repetition / Cognitive Psychology — FSRS / SuperMemo

**FSRS (Free Spaced Repetition Scheduler, Anki)** — This is the most dangerous prior art candidate.

- FSRS-6 has 21 trainable parameters fitted via gradient descent (log-loss/binary cross-entropy) against real user review history (~700M reviews, ~10K users for default values).
- Per-user calibration: "Optimize" button causes Anki to fit parameters from *your actual review history*, including a personalized decay exponent w20 (0.1–0.8).
- The decay model is a power-law forgetting curve: `R = (1 + F·t/S)^(-1/F)` where stability S and difficulty D are tracked per item.
- **Does it have a lifecycle FSM?** No. Cards are in one of {new, learning, review, suspended, buried} but these are scheduler states, not semantic-content lifecycle states (draft → active → deprecated → archived). There is no evidence-gated *retirement* of a card based on accumulated support evidence. Cards are scheduled; they are not deprecated based on multi-session usage patterns.
- **Does it calibrate decay to deployment evidence?** Yes — per user, per item. But the decay is on *retrieval probability* (probability the human recalls a fact), not on *rule utility* (whether an agent rule continues to fire helpfully in real sessions).

**SuperMemo SM-17/SM-18/SM-19:** The forgetting index framework uses retrievability R = 1 − exp(FI) and fits power-regression forgetting curves per item. Same structural gap: schedules memory strength, no semantic lifecycle states, no concept of rule conflict or rule support_count.

### 1.2 Information Retrieval — Document Freshness / Temporal BM25

- Google's freshness signal and academic temporal-BM25 variants apply exponential decay on document age for ranking. Parameters like the time-decay weight α in temporal BM25H are "selected empirically" (one paper notes α=1.02 by grid search over a corpus).
- TempRetriever (2502.21024, Feb 2026) embeds query date + document timestamp into dense retrieval.
- **Gap vs. N3:** IR freshness is about *document ranking*, not about promoting/retiring a rule record through discrete lifecycle states. Calibration is against retrieval metrics (MAP/NDCG), not against per-session deployment outcomes (support_count, conflict events). No FSM. No concept of "rule" as a named, reusable artifact.

### 1.3 Caching Theory — ARC, LFU with Aging, Redis LFU

- ARC (Adaptive Replacement Cache) dynamically balances LRU + LFU lists; parameter p is self-tuned online. Redis LFU uses logarithmic counters with a configurable decay period.
- Calibration: Cache policies are tuned by hit-rate on workload traces, not by domain-specific utility signals (rule conflicts, session outcomes).
- **Gap vs. N3:** No FSM with semantic states. Eviction is a binary operation (item in / item out), not a staged lifecycle (draft → active → deprecated → archived). No concept of a "rule" with support evidence.

### 1.4 Recommendation Systems — Temporal CF (Koren 2010)

- Koren's temporal CF models time-drifting user preferences using exponential decay functions on past ratings: `b_u(t) = b_u + α_u · sign(t − t_u) · |t − t_u|^β`. β is fitted by gradient descent against held-out ratings.
- **Gap vs. N3:** This decays user *preference weights*, not discrete rule records. No FSM. Calibration is against rating prediction loss, not against agent task-success rate or rule conflict counts.

### 1.5 Reinforcement Learning — Prioritized Experience Replay (PER, Schaul et al. 2016)

- PER uses TD-error as priority for sampling replay buffer entries. Priority exponent α and importance-sampling exponent β are tunable (α=0 → uniform). Entries are not explicitly retired; old entries fade by never being sampled.
- **Gap vs. N3:** No explicit lifecycle FSM. Calibration is implicit (TD-error is a training signal, not an external deployment metric). The replay buffer holds *transitions*, not *named rules*.

### 1.6 Ontology / Knowledge Representation — OWL Versioning, DL Maintenance

- W3C OWL versioning provides owl:versionInfo and owl:priorVersion annotations. TBox/ABox maintenance literature discusses consistency checking, but lifecycle management is human-driven versioning, not automated state transitions keyed on empirical usage signals.
- **Gap vs. N3:** No decay function. No automatic state transition based on support_count or hit-rate.

### 1.7 Records Management — ISO 15489

- ISO 15489-1:2016 defines record lifecycle: *create → capture → manage → dispose*. Retention schedules are policy-driven (legal requirements, fixed time windows), not empirically calibrated from usage signals.
- **Gap vs. N3:** No empirical calibration. Lifecycle states exist (create, active, dispose) but transitions are triggered by fixed policy, not by usage frequency or conflict detection.

### 1.8 SSGM Framework (2603.11768, March 2026) — Closest Agent-Memory Candidate

- SSGM proposes a Weibull decay function `w(Δτ) = exp(−(Δτ/η)^κ)` applied to memory relevance, with a freshness threshold θ_fresh below which memories are pruned.
- **Does it have lifecycle FSM states?** No formal draft/active/deprecated/archived. It has "mutable active graph" + "immutable episodic log" — a dual architecture, not a staged per-record lifecycle.
- **Is decay calibrated from deployment data?** No. Parameters are architectural proposals, explicitly acknowledged as not yet deployment-validated.

### 1.9 FadeMem (2601.18642, Jan 2026) — Noted Closest Prior Art

- Two-layer decay: LML shape parameter 0.8 (sub-linear), SML shape parameter 1.2 (super-linear). Half-lives: ~11.25 days (LML), ~5.02 days (SML).
- **Calibration:** The PDF does not document empirical fitting against deployment data. Parameters appear to be design choices (biologically inspired; values chosen to match cognitive timescales, not fitted to session outcomes).
- **FSM lifecycle:** Not present. No draft → active → deprecated → archived per memory record.

---

## Iteration 1 Summary

| Field | Lifecycle FSM? | Empirically Calibrated Decay? | Domain Match (rules/agent)? |
|---|---|---|---|
| FSRS/Anki | Scheduler states, not semantic lifecycle | YES — per-user, per-item (retrieval probability) | No — human flashcard recall, not agent rule utility |
| SuperMemo SM-17/18 | No | Yes (forgetting index, curve fitting) | No |
| IR freshness / BM25-temporal | No | Grid search on IR metrics | No |
| ARC / Redis LFU | No | Online self-tuning, not domain-specific | No |
| Koren temporal CF | No | Gradient descent on rating loss | No |
| PER (Schaul 2016) | No | Implicit (TD-error) | No |
| OWL versioning | Human-versioned | No | No |
| ISO 15489 | Yes — policy FSM | No — fixed policy | No |
| SSGM (2603.11768) | No | No — theoretical only | Partial |
| FadeMem (2601.18642) | No | Unclear, likely not | Partial |

---

## Iteration 2: Devil's Advocate

**What did I miss?**

1. **FSRS is the most dangerous**: It does empirically calibrate decay *per item* from *real usage data*. The structural question is whether "item-level decay calibration for human recall" and "rule-level decay calibration for agent utility" are the same claim. My assessment: they are structurally analogous but applied in different domains with different signals. FSRS calibrates P(recall | t, S, D) from human review responses. N3 would calibrate rule deprecation thresholds from agent session outcomes (support_count, conflict events, task-success delta). The signal is different (binary recall vs. multi-dimensional utility), the substrate is different (flashcard vs. structured rule record), and the FSM is absent in FSRS.

2. **Did I miss any RL / active-learning paper that manages a "rule library" with usage-based retirement?** AWM (Agent Workflow Memory) and RIMRULE extract rules but do not publish lifecycle management or decay calibration. SkillRL and MACLA maintain skill libraries but use coverage / frequency heuristics, not formal FSMs.

3. **ISO 15489 has the FSM structure** but its transitions are policy-driven (time elapsed, legal hold), not empirically calibrated from usage data. So N3's combination of (a) FSM + (b) empirical calibration is not present there.

4. **Koren temporal CF** is the strongest decay-calibration analog: it fits decay parameters from real data using gradient descent. But it operates on user preference weights, not named discrete rules, and has no lifecycle FSM.

**What is still missing from my search:** I have not searched explicitly for "rule lifecycle" in business rules engines (Drools, RETE), or for "concept drift" in data stream mining (which has online calibration of model staleness). These could be informative.

---

## Iteration 3: Final Targeted Searches

**Business rules engines (Drools/RETE):** Rule lifecycle in production rule engines is human-managed (enable/disable/version rules via UI). No empirical decay calibration based on firing frequency or outcome data. No automatic FSM transitions.

**Concept drift detection (river/MOA, ADWIN, DDM):** Concept drift detectors (Page-Hinkley, ADWIN) monitor statistical shift in a data stream and trigger model retraining. This is structurally relevant: it is usage-based automatic detection of staleness. However: (a) concept drift is about *model* staleness, not *named rule record* lifecycle; (b) there is no FSM with staged states (draft → active → deprecated → archived); (c) calibration is of detection sensitivity, not rule-level decay rate.

**Data quality / master data management (MDM):** MDM systems have record lifecycle states (candidate → golden → retired) but transitions are rule-based (match/merge confidence thresholds), not empirically calibrated decay rates tied to usage signals.

---

## Final Assessment

**Verdict-in-my-lane: PARTIAL-OVERLAP**

The combination claim — *per-record FSM with lifecycle states driven by empirically calibrated decay from deployment usage data* — is NOT present in any adjacent field as a unified construct. However:

- **FSRS pre-empts the "empirically calibrated decay" sub-claim** in the sense that calibrating forgetting/decay parameters from real usage data is a solved, published technique. The novelty cannot rest on "we calibrate decay from data" alone.
- **ISO 15489 / MDM / records management pre-empt the "lifecycle FSM" sub-claim**: staged states with defined transitions exist in records management, just not usage-calibrated.

**The specific gap is the combination**: no adjacent field applies empirically calibrated decay (in the FSRS sense — fitting decay rate from per-record usage outcomes) to named discrete rule records inside an LLM agent memory system with explicit FSM state transitions triggered by multi-dimensional usage signals (support_count + conflict events + hit-rate + time-since-use). This combination, specifically for *agent rules* (not flashcards, not documents, not cache entries), appears novel.

**Contribution reframe if N3 survives:** The claim should be positioned NOT as "empirically calibrated decay is new" (it is not — FSRS has done this since 2022), but as "applying calibrated decay to agent rule records with a formal lifecycle FSM, where the decay signal is agent task-success data rather than human retrieval probability." That reframe survives FSRS as prior art.
