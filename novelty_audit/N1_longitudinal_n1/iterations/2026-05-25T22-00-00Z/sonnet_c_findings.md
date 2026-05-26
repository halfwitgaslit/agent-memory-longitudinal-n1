# Researcher C — Adjacent Fields Findings
**Auditor:** Sonnet C (adjacent fields)
**Date:** 2026-05-25
**Claim:** N1 — Longitudinal n=1 agent-memory deployment

---

## Iteration 1 — Findings

### Top-10 Closest Works (ranked by similarity to N1 claim)

**1. Kazdin (2011) Single-Case Research Designs (Oxford University Press)**
- Field: Applied behavior analysis / clinical psychology
- Analogy: Their "single subject treated as own control across repeated phases" = our "one deployed user measured repeatedly as memory system evolves." Phase logic (A-baseline, B-intervention) maps directly onto memory-off vs. memory-on evaluation windows.
- Similarity: Very High. The methodological skeleton is identical. The subject is a human user; the intervention is agent memory.
- Source: https://global.oup.com/academic/product/single-case-research-designs-9780190079970

**2. Barlow & Nock (2009) / Kratochwill et al. (2010) SCED Guidelines**
- Field: Clinical psychology, SCED methodology
- Analogy: Their "phase change criteria," "visual analysis of level/trend/variability," and "intervention replication" = our proposed metrics for before/after memory activation in a single user session series.
- Similarity: Very High. SCED's demand for stable baselines before phase change mirrors the stabilization period needed before enabling persistent agent memory.
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC3652808/

**3. Guyatt et al. N-of-1 Trial Methodology (NEJM 1986; PMC8351788)**
- Field: Clinical medicine, personalized medicine
- Analogy: Their "repeated crossover within one patient to find optimal treatment" = our "alternating memory-enabled vs. memory-disabled sessions for one user to find optimal memory architecture." Statistical treatment of within-subject correlation (ρ) directly applies.
- Similarity: High. Core inferential logic is isomorphic. Key disanalogy: medical N-of-1 requires washout periods; AI memory has carryover that cannot be washed out, which is actually the interesting adaptation we would need to make.
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC8351788/

**4. Lillie et al. (2011) "The N-of-1 Clinical Trial: The Ultimate Strategy for Individualizing Medicine?" (Personalized Medicine)**
- Field: Personalized medicine
- Analogy: Their "individual response heterogeneity requires within-person evidence rather than population averages" = our core claim that aggregate AI benchmarks miss individual memory utility.
- Similarity: High. Philosophical alignment is near-perfect; methodological specifics differ (no washout analog for memory).
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC10388431/

**5. GitHub Copilot Longitudinal Mixed-Methods Study (arXiv:2509.20353)**
- Field: Empirical software engineering
- Analogy: Their "2-year longitudinal before/after Copilot adoption at NAV IT (25 users)" = our "longitudinal deployment of memory-augmented agent." However, theirs is group-level (n=25), not n=1.
- Similarity: Moderate-High. Design is closest in the SE literature but is not n=1 — it uses population-level inference. Key finding (no significant commit-metric change despite perceived productivity gain) is directly relevant to why n=1 repeated measures is needed.
- Source: https://arxiv.org/abs/2509.20353

**6. Recommender Systems Offline-Online Evaluation Gap (Jannach et al., AI Magazine 2022; DL:ACM)**
- Field: Recommender systems
- Analogy: Their "offline metrics fail to predict online individual-user outcomes" = our "static AI benchmarks fail to predict per-user memory utility in deployment." Their call for "longitudinal evaluation with humans in the loop" is nearly identical to our proposed methodology.
- Similarity: Moderate-High. Methodological problem is the same; their proposed solution (longitudinal, in-situ) matches ours. Not n=1, but individual-level longitudinal is discussed.
- Source: https://dl.acm.org/doi/10.1002/aaai.12051

**7. Personal Informatics / Quantified Self — Li et al. (2010) Stage-Based Model; CHI 2014 "Personal Tracking as Lived Informatics"**
- Field: HCI / personal informatics
- Analogy: Their "individuals collect, integrate, reflect on personal data over time to change behavior" = our "user interacts with memory-augmented agent, observes adaptation, reflects on utility." The 5-stage model (preparation, collection, integration, reflection, action) maps onto a longitudinal n=1 deployment cycle.
- Similarity: Moderate. Closest HCI analog but focuses on self-tracking tools rather than AI agent memory specifically.
- Source: https://dl.acm.org/doi/10.1145/2556288.2557039

**8. Cranfield Longitudinal IR Evaluation (arXiv:2409.05417; arXiv:2509.17440)**
- Field: Information retrieval
- Analogy: Their "static test collections miss temporal evolution of queries and relevance" = our "static benchmarks miss how agent memory utility evolves for one user over time." Longitudinal Cranfield extensions propose repeated evaluation over evolving collections — structurally analogous to repeated evaluation of a growing memory store.
- Similarity: Moderate. Methodological problem is the same (static eval ≠ dynamic deployment); their solution is corpus-level, not user-level.
- Source: https://arxiv.org/abs/2409.05417

**9. ABAB Reversal Design in Applied Behavior Analysis (ABA textbooks; PubMed 30527785)**
- Field: Applied behavior analysis
- Analogy: Their "withdraw intervention to show causal attribution, then re-introduce" = a potential design for memory deployment studies where memory is toggled to establish causal evidence. Ethical constraint in ABA (harmful to withdraw effective treatment) maps onto a real tension in memory studies (disabling a useful memory system harms users).
- Similarity: Moderate. Design logic applies but irreversibility of memory (unlike behavioral interventions) creates a key disanalogy.
- Source: https://pubmed.ncbi.nlm.nih.gov/30527785/

**10. Case-Based Reasoning Case-Base Maintenance Literature (CBR-related reviews; ResearchGate)**
- Field: Classical AI / knowledge-based systems
- Analogy: Their "case-base grows over time, performance changes nonlinearly with case accumulation" = our "agent memory grows over deployment, utility is non-monotone with memory volume." Case-base maintenance strategies (pruning, consolidation) directly mirror memory management in LLM agents.
- Similarity: Moderate. Oldest intellectual ancestor of agent memory; rarely cited in LLM memory papers despite direct lineage.
- Source: https://www.researchgate.net/publication/304295998_A_Review_and_Analysis_of_Case-Based_Reasoning_Research

---

## Iteration 2 — Findings

### Refined search: SCED applied to technology tools; N-of-1 applied to AI; recommender longitudinal individual

**Key new findings from iteration 2:**

**A. Technology-mediated intervention SCED studies exist (multiple baseline across behaviors)**
- Multiple baseline across behaviors designs have been applied to cognitive and technology-mediated interventions (e.g., remote CBT delivery for children via nonconcurrent multiple baseline). The logic extends directly to AI tool interventions.
- Implication: SCED has been applied to technology interventions broadly. No paper found applying SCED to AI agent memory specifically — this is the gap.
- Source: https://sambodhi.co.in/multiple-baseline-design-the-concept-application-and-analysis/

**B. N-of-1 carryover problem is our key adaptation point**
- Medical N-of-1 trials handle carryover with washout periods. For cumulative AI memory, there is no washout — memory persists and compounds. This means we need a modified N-of-1 without crossover reversal: a "one-arm longitudinal trajectory" design, closer to the ABAB without the second A.
- This is methodologically novel: N-of-1 without washout, focused on trajectory rather than treatment comparison.
- Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC5711967/

**C. Recommender Systems: "Longitudinal evaluation with humans in the loop" call (Jannach 2022)**
- The RS community explicitly calls for longitudinal, individual-user evaluation. Papers show offline metrics routinely fail to predict online individual outcomes. The RS field has *identified* the problem but has *not* solved it with a formal single-user methodology.
- Implication: Strong methodological precedent that this problem space exists and is unsolved at the n=1 level.

**D. Copilot longitudinal study (arXiv:2509.20353): closest empirical analog in SE**
- 2-year study, mixed-methods, before/after adoption. Group-level, not n=1. Key finding: self-reported productivity ≠ commit-metric productivity. This is precisely the motivation for n=1 repeated measures.
- Implication: This study is the closest prior art in the software engineering domain but is explicitly NOT n=1.

**E. Personal AI memory (arXiv:2409.11192) — survey paper, no deployment study**
- Identifies ethical and technical considerations for AI assistants with long-term memory. No longitudinal deployment evaluation methodology proposed.
- Implication: The gap we claim is confirmed in the literature.

---

## Iteration 3 — Findings

### Refined search: BDI agents longitudinal; SCED + AI; n-of-1 LLM; personalization evaluation single-user

**Key new findings from iteration 3:**

**F. No n-of-1 / SCED methodology applied to LLM agent memory found**
- Searches for "n-of-1 AI agent memory evaluation," "single case LLM," and "SCED AI tool evaluation" return zero direct hits. The methodology gap is confirmed: these two bodies of literature have not been connected.

**G. CLONEMEM benchmark (arXiv:2601.07023) — closest AI-side approach**
- Evaluates AI memory via "longitudinal coherence" but uses static benchmark structure (prebuilt personas), not real single-user deployment. No individual trajectory measurement.
- Implication: Even the most methodologically aware AI memory benchmarks do not use SCED / N-of-1 designs.

**H. PersonaLens (2025) — personalization benchmark**
- Evaluates conversational AI personalization but uses simulated personas and population-level metrics. Not longitudinal real deployment, not single-user.
- Source: https://arxiv.org/abs/2506.09902

**I. BDI agent evaluation: one paper proposes "longitudinal feedback loops with dynamic assessment" (arXiv:2510.03984)**
- "Beyond Static Evaluation: Rethinking the Assessment of Personalized Agent Adaptability in Information Retrieval" (2025) proposes simulated personas with temporally evolving preferences and longitudinal feedback loops. Closest ML-adjacent analog to our design.
- Key distinction: uses simulated personas, not real deployed user. Does not use SCED or N-of-1 framing.
- Source: https://arxiv.org/abs/2510.03984

**J. CHI'26 Workshop on Cognitive Personal Informatics (arXiv:2601.14891)**
- Workshop papers touch on longitudinal personal data, memory, and AI. No paper found using formal SCED or N-of-1 methodology.
- Confirms the HCI community is circling this problem but has not formalized the methodology.

---

## Summary Ranking (Top-5 for falsification risk)

| Rank | Work | Field | Similarity | Falsification risk |
|------|------|-------|------------|-------------------|
| 1 | Kazdin (2011) SCED | Psych/ABA | Very High (methodology) | Methodology is prior art; application to AI memory is not |
| 2 | Guyatt N-of-1 (1986–2023) | Medicine | High (design logic) | Design logic is prior art; AI adaptation is novel |
| 3 | Copilot longitudinal (arXiv:2509.20353) | SE | Moderate-High (domain) | Group-level, not n=1; confirms gap |
| 4 | Jannach RS eval (2022) | RecSys | Moderate-High (problem) | Identifies same problem; no n=1 solution |
| 5 | arXiv:2510.03984 BDI/IR personalization | IR/AI | Moderate (closest AI-side) | Simulated, not real deployment; no SCED framing |
