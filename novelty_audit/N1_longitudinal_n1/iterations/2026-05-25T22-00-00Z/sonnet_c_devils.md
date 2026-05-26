# Researcher C — Devil's Advocate
**Auditor:** Sonnet C (adjacent fields)
**Date:** 2026-05-25
**Claim:** N1 — Longitudinal n=1 agent-memory deployment

---

## Iteration 1 — Devil's Advocate

**(1) Strongest falsification candidate from this iteration:**
SCED methodology (Kazdin 2011; Barlow & Nock) is not merely analogous — it *is* the methodology we are proposing to apply. The design logic of "treat one subject as own control, measure repeatedly across phases, analyze for level/trend/variability change" is fully specified in 40 years of psychology literature. We are not inventing a methodology; we are applying an existing one.

**(2) Which field's methodology is the closest match?**
Applied behavior analysis / single-case experimental design (SCED) in clinical and educational psychology is the closest match by far. The n-of-1 trial literature in medicine is a second-order cousin (SCED + randomization + washout). Both fields have complete statistical frameworks, reporting standards (Kratochwill et al. 2010 WWC standards; CONSORT N-of-1 extension), and meta-analytic aggregation methods.

**(3) Could we cite it as "we adapt SCED methodology to agent-memory deployment"?**
Yes — and this is the *honest* and *stronger* framing. Rather than claiming methodological novelty, we should claim: "We are the first to instantiate SCED methodology in the domain of AI agent memory deployment, adapting phase logic to memory-on/memory-off windows and adapting visual analysis to memory utility metrics (task completion rate, retrieval precision, user correction frequency)." This is a contribution of application, not of invention. The methodology is borrowed; the application is new.

**(4) What remains novel if we concede methodology?**
The specific operationalization is novel: (a) defining what counts as a "phase" in agent memory deployment (session count? calendar time? memory volume?); (b) defining dependent variables for AI memory utility (no established measurement battery exists); (c) handling the irreversibility problem (memory cannot be washed out the way a drug can); (d) the specific adaptation to LLM agent architectures. The *problem of measuring intra-individual change in AI memory utility over real deployment* has no prior solved instance.

---

## Iteration 2 — Devil's Advocate

**(1) Strongest falsification candidate from this iteration:**
The N-of-1 clinical trial framework (Guyatt, Lillie, PMC8351788, PMC5711967) is a near-complete methodological prior. It handles: repeated within-subject measurement, temporal autocorrelation via time-series analysis, individual heterogeneity framing, and aggregation across multiple n=1 trials into population estimates. Every one of these elements is part of what we propose. The CONSORT 2015 N-of-1 extension provides reporting standards that we would adopt nearly verbatim.

**(2) The carryover problem as a source of novelty:**
Medical N-of-1 trials use washout periods to neutralize carryover. AI agent memory is *defined by* cumulative carryover — memory compounds across sessions by design. This means the standard crossover N-of-1 design is inapplicable in its canonical form. We need a monotone longitudinal trajectory design without reversal: a "one-arm interrupted time series" adapted from epidemiology rather than a crossover trial. This is a genuine methodological adaptation, not just application.

**(3) Could we cite SCED/N-of-1 as precursor?**
Strongly yes. Framing: "We adapt the interrupted time series variant of N-of-1 methodology (cf. Guyatt 1986; Lillie 2011) to the irreversible cumulative treatment case, applying it for the first time to AI agent memory deployment. The absence of washout feasibility necessitates [our specific design adaptation]." This is honest, positions us in a known methodological tradition, and makes our adaptation legible and defensible.

**(4) Empirical SE gap (Copilot study):**
The Copilot longitudinal study (arXiv:2509.20353) is methodologically sophisticated but explicitly group-level. Its finding — perceived productivity ≠ measured productivity — is the *motivation* for n=1 methodology, not prior art for it. We can cite it as evidence that group-level longitudinal methods are insufficient.

---

## Iteration 3 — Devil's Advocate

**(1) Strongest remaining falsification candidate:**
arXiv:2510.03984 ("Beyond Static Evaluation: Rethinking the Assessment of Personalized Agent Adaptability in IR") proposes longitudinal feedback loops and temporally evolving simulated personas for IR agent evaluation. If a future paper extends this to real users with real memory, it would be very close prior art. As of now, it is simulated, not deployed, and does not use SCED/N-of-1 framing.

**(2) Honest verdict on methodology novelty:**
The methodology is NOT novel in the abstract — SCED and N-of-1 designs are 40-60 year old established frameworks. What IS novel: (a) applying these to AI agent memory, (b) the specific adaptations required (irreversibility, session-boundary phase definition, LLM-specific dependent variables), (c) the construction of a valid measurement instrument for agent memory utility at the individual level.

**(3) Could we publish the methodology as a contribution?**
Yes, with appropriate framing. The contribution is not "we invented SCED" but "we identified that SCED is the correct methodology for individual-level agent memory evaluation, specified the necessary adaptations, and demonstrated applicability." This is a methodological translation contribution — valuable and publishable, especially at CHI, CSCW, or a methodology-focused AI venue.

**(4) What the three iterations reveal collectively:**
No paper has done this. The closest adjacent work (SCED, N-of-1) has not been cited in any AI memory evaluation paper found. The closest AI-side work (CLONEMEM, PersonaLens, arXiv:2510.03984) does not use SCED/N-of-1 frameworks. The bridge is unbuilt. The claim SURVIVES as a novel *application* but faces clear partial overlap at the *methodological* level. The honest framing is: "We adapt established single-subject methodology (SCED/N-of-1) to a new domain for the first time."
