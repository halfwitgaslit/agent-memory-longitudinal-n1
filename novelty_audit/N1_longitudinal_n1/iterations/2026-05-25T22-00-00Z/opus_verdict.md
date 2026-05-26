# Opus Verdict — N1 Longitudinal n=1 Agent-Memory Deployment

**Date:** 2026-05-25
**Consolidator:** Opus 4.7
**Audit target:** A single developer (or small team), deploying agent-memory systems (Mem0, Letta, Hindsight, etc. or hand-built) against their real coding work over weeks/months, with pre-registered protocol, randomized memory configurations across worktrees/sessions, and time-series outcome measurement (task success, time-to-solution, retry count, self-rated quality).

---

## 1. Final verdict

**`partial-overlap`**

The conjunction of (a) pre-registered SCED/N-of-1 protocol, (b) deployed agent-memory-as-treatment with randomized configurations, (c) coding-CLI substrate, and (d) >50 real sessions has not been published. But two adjacent literatures jointly cover ~80% of the territory: SCED/N-of-1 methodology is a 40–60 year old framework (Kazdin 2011; Guyatt 1986; Kratochwill 2010), and Daniel Miessler's PAI is an ~2-year n=1 longitudinal personal-AI-memory deployment with quantified signals (3,540), failure-event analysis (84), versioned algorithm changelog, and a conference talk at [un]prompted 2026. The contribution is a *methodological translation*, not a methodological invention, and the practitioner deployment template already exists in non-academic form.

## 2. Confidence

**High.** Three independent researchers ran 3-iteration adversarial sweeps across arxiv, ACL/EMNLP/COLM/CHI/CSCW/ICSE/FSE/MSR proceedings, HuggingFace, GitHub, vendor blogs (Mem0/Letta/Hindsight/Cognee/Mastra/ByteRover/EverMemOS), Hacker News, LessWrong, Substack, Medium, podcast archives, and adjacent fields (clinical psychology SCED, medical N-of-1, personal informatics, recommender systems, IR, BDI agents, case-based reasoning, autoethnography, quantified self). The Miessler hit was found in iteration 3 of the B lane after explicit search for practitioner deployments — late-iteration discovery of a near-kill is the mark of an exhaustive sweep. Residual risk is in unindexed venues (CSCW workshop proceedings, dissertations, Letta/Mem0 Discord archives, the rate-limited HN item 46398323) but not in mainstream literature.

## 3. Top 3 closest prior works

### #1 — Daniel Miessler, "Building Your Own Personal AI Infrastructure" (Jul 2025, updated Jan/Apr 2026)
- **Full citation:** Miessler, D. (2025/2026). *Building Your Own Personal AI Infrastructure (PAI)*. danielmiessler.com/blog/personal-ai-infrastructure. Companion talk at [un]prompted 2026; deep-dive podcast at Cognitive Revolution (2025–2026).
- **Similarity quote (from Sonnet B):** "Solo developer, n=1 deployment of custom memory system (3-tier: Session/Work/Learning Memory) running ~2 years; 3,540 signals captured; 84 rating-1 failure events analyzed to derive behavioral steering rules; 'Algorithm' versioned v0.1–v0.2.23; publicly documented reflective learning from behavior; conference talk at [un]prompted 2026."
- **What they did NOT do that we would:** (i) no pre-registered protocol — feedback signals collected and steering rules derived post-hoc, not against a hypothesis registered before deployment; (ii) no randomized memory configurations across worktrees/sessions — single-arm trajectory, not a controlled comparison between memory architectures; (iii) substrate is general personal-AI infrastructure (assistant-style), not a coding-CLI (Claude Code / Codex / Cursor) substrate with task-success / retry-count / time-to-solution as primary endpoints; (iv) no time-series statistical analysis with within-subject autocorrelation (ρ) modeling; (v) custom architecture, not a comparison of named OSS memory frameworks (Mem0 vs Letta vs Hindsight vs Cognee vs hand-built).

### #2 — Kazdin (2011) Single-Case Research Designs + Kratochwill et al. (2010) WWC SCED Standards + Guyatt et al. N-of-1 Methodology (NEJM 1986; PMC8351788)
- **Full citation:** Kazdin, A.E. (2011). *Single-Case Research Designs: Methods for Clinical and Applied Settings* (2nd ed.). Oxford University Press. ISBN 9780190079970. Kratochwill, T.R., et al. (2010/2013). "Single-Case Designs Technical Documentation," *What Works Clearinghouse*. PMC3652808. Guyatt, G., et al. (1986). "Determining optimal therapy: randomized trials in individual patients," *NEJM*. Kravitz, R.L., et al. (2021). "Personalized (N-of-1) Trials: A Primer," PMC8351788.
- **Similarity quote (from Sonnet C):** "'Single subject treated as own control across repeated phases' = our 'one deployed user measured repeatedly as memory system evolves'. Phase logic (A-baseline, B-intervention) maps directly onto memory-off vs. memory-on evaluation windows."
- **What they did NOT do that we would:** they specify a *general* methodology and apply it to clinical/educational behavior change and pharmacology; none of these works (or any cited extension up through 2026) instantiate SCED/N-of-1 in the AI agent-memory domain, none address the irreversibility problem (no washout possible for cumulative memory carryover), and none specify dependent variables appropriate for LLM coding-assistant utility (task success, time-to-solution, retry count, self-rated quality). The CONSORT N-of-1 2015 extension provides reporting standards we would adapt verbatim.

### #3 — Sandelin, "The First Controlled Benchmark of AI Memory in Coding Agents" (Stompy, 2025–2026)
- **Full citation:** Sandelin, M. (2025/2026). *The First Controlled Benchmark of AI Memory in Coding Agents*. medium.com/@mrsandelin/...8e0bb776d39e.
- **Similarity quote (from Sonnet A):** "Single codebase, controlled memory conditions (on/off/hybrid), real coding tasks, outcomes include task quality and completion efficiency. Author mentions future longitudinal study."
- **What they did NOT do that we would:** only 9 runs (3 tasks × 3 conditions), not pre-registered, not time-series, not single-developer tracked over weeks/months, blog not peer-reviewed. Critically, **the author explicitly announces a planned 27-session longitudinal follow-up that has not yet appeared in any search result** — effectively a public flag that the full study does not yet exist as of 2026-05-25. This is the closest *coding-substrate* analog and demonstrates community awareness that the gap is real and unfilled.

(Honorable mentions cited in lane sources: METR RCT arXiv:2507.09089 — closest within-subject randomized real-coding-work design, but no memory system; NAV IT Copilot arXiv:2509.20353 — 2-year longitudinal real-developer, but n=25 and no memory; "Algorithmic Self-Portrait" arXiv:2602.01450 — n=80 ChatGPT memory donation study, but retrospective not prospective and not self-deployment.)

## 4. The exact surviving gap

What no surveyed work has done, and what we would do:

**The conjunction:**

1. **Pre-registered SCED/N-of-1 protocol** (Kratochwill 2010 / CONSORT N-of-1 2015 reporting standards) — registered with hypotheses, dependent variables, phase-change criteria, and analysis plan locked before deployment.
2. **Multi-arm comparison of *named* OSS agent-memory frameworks** as the treatment factor (Mem0 vs Letta vs Hindsight vs Cognee vs hand-built control) — randomized across git worktrees and/or sessions, not single-arm trajectory.
3. **Coding-CLI substrate** (Claude Code / Codex / Cursor) on the developer's own real work, with task success, time-to-solution, retry count, and self-rated quality as primary endpoints — not personal-assistant infrastructure (Miessler), not synthetic benchmarks (LongMemEval / LoCoMo / MemoryArena / SWE-Bench-CL / CloneMem / MemoryCode / PersonaMem-v2), not general AI tools (METR).
4. **>50 real sessions over weeks–months** with time-series analysis explicitly modeling within-subject autocorrelation and the irreversibility/cumulative-carryover adaptation of standard N-of-1 (no washout possible — a methodological novelty).

Miessler covers (3-adjacent, longitudinal, n=1) but is single-arm, post-hoc, and not coding-CLI specific. SCED/N-of-1 covers (1, 4-methodology) but never instantiated in agent-memory. Sandelin covers (2, 3) but n=9 and not longitudinal. **No work covers the full conjunction.**

## 5. Repositioning recommendation

Even with the claim surviving, the framing **must be repositioned** to be defensible to a hostile reviewer who will cite Miessler and SCED as "this has been done":

**Recommended framing:** *"The first pre-registered, randomized, multi-framework SCED/N-of-1 deployment study of OSS agent-memory systems on a coding-CLI substrate, adapting medical N-of-1 methodology to the irreversible-cumulative-treatment case."*

Concrete moves:
- **Cite Miessler in the very first paragraph** as the practitioner precedent and explicitly differentiate on (a) pre-registration, (b) randomized framework comparison, (c) coding-substrate, (d) statistical N-of-1 framework. Trying to ignore Miessler will get the paper desk-rejected.
- **Cite Kazdin, Kratochwill, Guyatt, Kravitz** as the methodological lineage. Position the work as a *methodological translation*: "We adapt SCED to AI agent memory, specifying the necessary adaptations (irreversibility, session-boundary phase definition, LLM-CLI-specific dependent variables)."
- **Adopt CONSORT N-of-1 (2015) reporting standards verbatim** — this is the most defensible move. A reviewer who challenges methodological novelty cannot also challenge reporting rigor.
- **The "no washout" adaptation IS the methodological contribution.** Frame it as: standard N-of-1 crossover is inapplicable because memory compounds; we propose an interrupted-time-series + multi-arm-by-worktree design that solves the irreversibility problem. This is a clean publishable methods contribution distinct from mere application.
- **Drop the word "first" anywhere it appears.** Use "first pre-registered" or "first multi-framework randomized" — never standalone "first." Reviewers will dig for prior art on bare "first" claims.
- **Coding-CLI substrate must be load-bearing in the title.** Without it the claim collapses into Miessler. Suggest title: *"Pre-Registered N-of-1 Evaluation of Agent-Memory Frameworks on a Coding-CLI Substrate."*

## 6. Falsification-test residual risk

Searches we did NOT do that could still kill the claim post-publication:

1. **Letta / Mem0 / Cognee Discord and Slack archives.** Not indexed by search engines. Solo-developer experiments are very likely posted in `#showcase` / `#experiments` channels. Highest residual risk.
2. **Hacker News item 46398323 ("An experiment in separating identity, memory, and tools")** — rate-limited during the audit. Could be a direct hit if it documents a longitudinal protocol.
3. **CSCW 2025/2026 workshop proceedings** (not on arxiv, behind ACM DL paywall) — autobiographical-design and technology-probe work would live here. Searched secondarily.
4. **PhD dissertations and ProQuest theses** — not crawled. A dissertation on "n=1 LLM coding-assistant deployment" could exist.
5. **SSRN / OSF Preprints** — organizational behavior / personal-science work hosted here. Not searched directly.
6. **Sandelin's planned 27-session longitudinal follow-up** — if published between today (2026-05-25) and our publication date, it preempts on the *coding-substrate* axis. Monitor `medium.com/@mrsandelin` and any associated Substack/X account weekly.
7. **CHI'26 late-breaking and CHI'27 archive** — not yet released. Direct competitive risk.
8. **Closed-source enterprise deployments** (Microsoft Copilot Memory, Salesforce Einstein, Cursor Memory Bank, MemNexus/Recallium logs) — millions of de facto n=1 deployments exist but are unpublished. A vendor whitepaper appearing later would not kill *academic* novelty but would weaken practical-novelty claims.
9. **OSF.io pre-registration registry.** Not searched. If anyone has pre-registered a similar protocol but not yet published, the OSF entry would already establish priority.
10. **arxiv withdrawn-and-revised papers / arxiv RSS feeds since 2026-05-20.** A May-2026 preprint matching the claim could have been posted in the last week.

Pre-publication watchlist mitigation: set up weekly alerts on (Mem0|Letta|Hindsight|Cognee|N-of-1|SCED|longitudinal n=1) combined with (coding agent|coding assistant|memory) across arxiv, OSF, and Sandelin's outlets.

## 7. Per-researcher lane verdicts

- **Sonnet A (academic):** `SURVIVED-MY-LANE` — "No paper found that combines ALL of: real developer + agent memory system deployed + >50 longitudinal sessions + pre-registered protocol + randomized memory configurations + time-series outcome measurement."
- **Sonnet B (industry/OSS):** `PARTIAL-OVERLAP` — "Daniel Miessler's PAI is a near-kill... Claim survives if it requires (a) named framework, (b) prospective study design with defined outcomes, or (c) peer-reviewed publication."
- **Sonnet C (adjacent fields):** `PARTIAL-OVERLAP` — "The methodology (SCED / N-of-1 trial design) is 40-60 year old prior art... The specific application to AI agent memory deployment, the necessary adaptations (irreversible carryover, session-boundary phase definition, LLM-specific DVs), and the construction of a measurement instrument are novel."

**Disagreement resolution:** Sonnet A's `SURVIVED` is correct *for the academic literature* but is the weakest lane because it underweights practitioner prior art. Sonnet B and Sonnet C converge on `PARTIAL-OVERLAP` from different angles (Miessler on the practitioner-deployment side, SCED/N-of-1 on the methodology side). **The conjunction of Miessler + SCED jointly closes ~80% of the gap.** Closing the remaining ~20% requires the specific framing in §5: pre-registration + randomized multi-framework comparison + coding-CLI substrate + irreversibility-adapted N-of-1 design. I therefore consolidate to **`partial-overlap`** rather than Sonnet A's lane-only `SURVIVED`.

## 8. Reviewer-grade summary (≤150 words)

> *Verdict: partial-overlap.* The authors propose a longitudinal n=1 study of OSS agent-memory frameworks on a coding-CLI substrate. Two adjacent literatures jointly cover most of the territory and must be confronted head-on. Miessler's *Personal AI Infrastructure* (2025/2026, [un]prompted talk) is a publicly documented ~2-year n=1 deployment of a custom 3-tier memory system with 3,540 quantified signals and 84 analyzed failure events; SCED (Kazdin 2011; Kratochwill 2010; WWC standards) and medical N-of-1 (Guyatt 1986; Kravitz 2021; CONSORT N-of-1 2015) supply a complete methodological apparatus. The defensible kernel — pre-registered, randomized multi-framework comparison on a coding-CLI substrate, with an explicit interrupted-time-series adaptation of N-of-1 for irreversible cumulative treatment — is genuinely uncited. Authors must cite Miessler in paragraph one and Kazdin/Kratochwill in the methods section, or this paper will be desk-rejected as undifferentiated work. Conditional accept on repositioning.
