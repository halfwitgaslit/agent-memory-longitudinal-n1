# Sonnet A — Academic Findings
**Audit target:** N1 — Longitudinal n=1 agent-memory deployment  
**Researcher role:** Academic literature (adversarial/falsification stance)  
**Date:** 2026-05-25

---

## Iteration 1 — Findings

### Search strategy
- arxiv: "longitudinal LLM agent memory deployment real-world field study single-subject design"
- arxiv: "n-of-1 evaluation LLM agent memory personalization in-the-wild deployment"
- arxiv + web: Mem0/Letta/Hindsight real user study longitudinal evaluation coding assistant
- AI pair programming longitudinal studies: Copilot, Cursor, Codex deployment 2024–2025
- CHI 2024–2025: HCI deployment study AI coding assistant memory

### Top papers ranked by similarity to the claim (Iteration 1)

**Rank 1 — NAV IT Copilot longitudinal study**
- URL: https://arxiv.org/abs/2509.20353
- Published: 2025/2026 (published at ICSE 2026)
- Summary: Mixed-methods longitudinal case study at NAV IT: 25 Copilot users + 14 non-users, 26k commits over 2 years, 13 interviews, survey. Examines real developer productivity outcomes over multi-year period.
- Similarity: Longitudinal real-developer deployment with time-series outcomes (commit activity, perceived productivity). Real coding work. Multiple sessions per developer.
- Difference: No memory system evaluated (Copilot, not Mem0/Letta/Hindsight). No pre-registered protocol mentioned. No randomized memory configurations across sessions/worktrees. Not n=1. Not time-series on task-success/retry/self-rated quality. N=39 developers, not solo.

**Rank 2 — Evolving with AI: Longitudinal Analysis of Developer Logs**
- URL: https://arxiv.org/abs/2601.10258
- Published: 2026 (ICSE 2026)
- Summary: 800 developers tracked over 2 years via fine-grained IDE telemetry. Analyzes 5 workflow dimensions: productivity, code quality, editing, reuse, context switching. AI coding assistants, not memory agents.
- Similarity: Longitudinal real-developer deployment, telemetry-based outcome measurement, multi-year data.
- Difference: No agent memory system evaluated. No pre-registered protocol. Not n=1. N=800 + survey of 62. No randomized memory configurations. Observational, not interventional.

**Rank 3 — METR RCT: Measuring the Impact of Early-2025 AI on Developer Productivity**
- URL: https://arxiv.org/abs/2507.09089
- Published: July 2025
- Summary: RCT with 16 experienced open-source developers, 246 tasks, task-level randomization to AI-allowed vs. AI-disallowed conditions. Cursor Pro + Claude 3.5/3.7. Found AI tools increased completion time by 19%.
- Similarity: Randomized assignment of conditions across real developer sessions; outcomes measured (task completion time). Real coding work, real developers. Closest to a within-subject experimental design.
- Difference: No memory system evaluated. No pre-registered protocol mentioned. Not n=1. Not specifically about agent memory. 16 developers, not single-developer. No time-series on memory-on vs memory-off across worktrees.

**Rank 4 — Enabling Personalized Long-term Interactions in LLM-based Agents (5-day pilot)**
- URL: https://arxiv.org/abs/2510.07925
- Published: October 2025
- Summary: Framework integrating persistent memory and user profiles for personalized LLM agents. Evaluated on public datasets plus a 5-day pilot user study.
- Similarity: Real user study of agent memory system (persistent memory); pilot deployment; outcomes include perceived personalization.
- Difference: 5-day pilot only (not weeks/months). No pre-registered protocol. Not n=1. Not coding-specific. Session count not reported. No randomized memory configurations.

**Rank 5 — LoCoMo: Long-Term Conversational Memory Benchmark**
- URL: https://snap-research.github.io/locomo/ (ACL 2024)
- Published: ACL 2024
- Summary: Large-scale benchmark of long-term conversational memory with machine-generated/human-verified dialogues, up to 35 sessions, 300 turns, 9K tokens. Evaluates LLM memory retrieval and reasoning.
- Similarity: Multi-session memory evaluation; tests longitudinal retention across 35 sessions; outcome-based measurement (QA accuracy, summarization).
- Difference: Synthetic dialogues, not real user deployment. Not coding-specific. Not pre-registered. Not n=1. No real developer sessions. Not task-success/time-to-solution metrics.

**Rank 6 — Hindsight: Building Agent Memory that Retains, Recalls, and Reflects**
- URL: https://arxiv.org/abs/2512.12818
- Published: December 2024
- Summary: Technical paper proposing a structured multi-network memory architecture achieving 91.4% on LongMemEval. Systems paper with benchmark evaluation.
- Similarity: Agent memory system with performance evaluation across sessions. Multi-session design.
- Difference: No real user deployment. No human developer in the loop. No pre-registered protocol. Not n=1. Not longitudinal field study. Benchmark-only.

**Rank 7 — Developer Productivity with and without GitHub Copilot (NAV IT, longitudinal)**
- URL: https://arxiv.org/abs/2509.20353 (same as Rank 1 — confirmed)

**Rank 7 — "First Controlled Benchmark of AI Memory in Coding Agents" (Sandelin/Stompy)**
- URL: https://medium.com/@mrsandelin/the-first-controlled-benchmark-of-ai-memory-in-coding-agents-8e0bb776d39e
- Published: 2025/2026 (blog post)
- Summary: Author tests memory on/off/hybrid conditions across 9 runs (3 tasks x 3 conditions) on their own codebase (Stompy). Measures task completion quality, token cost, turns. Explicitly a pilot study. Plans a 27-session longitudinal follow-up.
- Similarity: **Most structurally similar to the claim.** Single codebase, controlled memory conditions, real coding tasks, outcomes include task quality and completion efficiency. Author mentions future longitudinal study.
- Difference: Only 9 runs (not >50 sessions). Not pre-registered. Not time-series. Not single-developer tracked over weeks/months. Blog post, not peer-reviewed. Future longitudinal study explicitly NOT yet published.

**Rank 8 — SWE-Bench-CL: Continual Learning for Coding Agents**
- URL: https://arxiv.org/abs/2507.00014
- Published: July 2025
- Summary: Benchmark organizing GitHub issues chronologically to test agent continual learning across sequential tasks. FAISS-backed semantic memory. Evaluates forgetting, forward/backward transfer.
- Similarity: Sequential task structure simulating longitudinal developer engagement; agent memory evaluated; coding-specific tasks; multiple outcome metrics.
- Difference: Synthetic benchmark, not real developer deployment. No human in the loop. Not pre-registered. Not n=1. Not self-rated quality.

**Rank 9 — From Tools to Teammates: Evaluating LLMs in Multi-Session Coding Interactions (ACL 2025)**
- URL: https://arxiv.org/abs/2502.13791
- Published: ACL 2025
- Summary: Tests LLM multi-session coding coherence using MemoryCode, a synthetic dataset. Found GPT-4o degrades when instructions span sessions.
- Similarity: Multi-session memory evaluation in coding context; identifies failure modes relevant to agent memory.
- Difference: Synthetic data only. No real developer sessions. No pre-registered protocol. Not n=1. Not longitudinal real-world.

**Rank 10 — LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues**
- URL: https://arxiv.org/abs/2605.12493
- Published: May 2026
- Summary: Benchmark for evaluating whether memory systems help agents behave as knowledgeable colleagues. 451 manually curated questions. Includes AgentRunbook-C coding variant.
- Similarity: Coding-specific agent memory evaluation; multi-session; measures experience accumulation.
- Difference: Synthetic benchmark. No real developer deployment. No pre-registered protocol. Not n=1. Not real-world field study.

---

## Iteration 2 — Findings

### Search strategy (Iteration 2 — deepened)
- CHI/CSCW/UIST deployment study AI memory personalization individual user weeks real tasks
- single-subject experimental design AI assistant coding productivity
- pre-registered LLM agent memory individual developer evaluation
- ACL/EMNLP 2024–2025 memory-augmented LLM real user deployment
- COLM 2024–2025 agent memory deployment personalization evaluation real developer
- n-of-1 trial methodology applied to AI developer productivity crossover randomization
- MSR 2024–2025 AI coding agent memory longitudinal telemetry

### Additional papers examined

**METR "Changing Design" (Feb 2026 update)**
- URL: https://metr.org/blog/2026-02-24-uplift-update/
- Published: February 2026
- Summary: METR retrospective on their late-2025 study failures and pivot. Identifies that task-level randomization across 57 developers failed due to selection bias and agentic tool measurement problems. No n=1, no memory system.
- Similarity: Methodological self-critique of longitudinal AI developer study, identifies the challenges of measuring AI coding productivity in realistic conditions.
- Difference: Not about memory systems. Describes abandoned methodology, not a completed study. Not n=1.

**IBM watsonx Code Assistant CHI EA '25**
- URL: https://arxiv.org/abs/2412.06603
- Published: December 2024 / CHI EA '25
- Summary: 669 survey respondents + 15 usability test participants on watsonx Code Assistant at IBM. Examines productivity expectations and code ownership concerns.
- Similarity: Real enterprise deployment study of AI coding assistant; real developers.
- Difference: No memory system. No longitudinal tracking. No pre-registered protocol. Not n=1. No time-series outcomes.

**Autonomous Memory Augmentation for LLM Agents (EMNLP 2025)**
- URL: https://aclanthology.org/2025.emnlp-main.1683.pdf (PDF too large to fetch)
- Published: EMNLP 2025
- Summary: Not fully retrievable but title suggests autonomous memory augmentation. Based on title alone — not a real-user deployment study.

**Reflective Memory Management for Long-term Interactions (ACL 2025)**
- URL: https://aclanthology.org/2025.acl-long.413.pdf
- Published: ACL 2025
- Similarity: Long-term memory management for conversational agents; multi-session.
- Difference: Based on title/metadata — likely benchmark/systems paper, not real-user field study.

**OpenAgents (arXiv 2310.10634)**
- URL: https://arxiv.org/abs/2310.10634
- Published: October 2023 (STALE-RISK)
- Summary: Open platform for language agents; includes Data Agent (Python/SQL) and Plugins Agent. Real users interact with agents.
- Similarity: Real user interactions with agents in the wild; coding-relevant (Data Agent).
- Difference: Not longitudinal. Not about memory system evaluation. Not pre-registered. Not n=1. Not developer-session tracking.

### Key finding from Iteration 2:
No CHI, CSCW, UIST, ACL, EMNLP, or COLM paper found that matches: (a) real developer, (b) memory system deployed, (c) longitudinal >50 sessions, (d) pre-registered, (e) n=1 or single-subject. The METR 2025 RCT is the closest study to rigorous within-person design but evaluates general AI tools, not memory systems, and uses N=16, not n=1.

---

## Iteration 3 — Findings

### Search strategy (Iteration 3 — final sweep)
- Papers With Code agent memory benchmark "within-person" OR "n=1" OR "single subject"
- IEEE Xplore ACM "agent memory" "longitudinal" OR "field deployment" coding developer empirical
- "AI coding assistant" "memory" "randomized" individual developer weeks months sessions outcome
- SWE-Bench-CL: Continual Learning for Coding Agents
- "developer productivity" "memory" "agent" "pre-registered" single developer
- n-of-1 trial methodology applied to AI tools developer productivity

### Key additional papers

**SWE-Bench-CL**
- URL: https://arxiv.org/abs/2507.00014
- Published: July 2025
- Confirmed synthetic benchmark only. No real developer in the loop. No pre-registration.

**Stompy "First Controlled Benchmark" (Sandelin blog)**
- URL: https://medium.com/@mrsandelin/the-first-controlled-benchmark-of-ai-memory-in-coding-agents-8e0bb776d39e
- Published: 2025/2026 (blog, not peer-reviewed)
- Critical finding: This is the closest thing found to the N1 claim in the entire literature sweep. Author explicitly states a **planned** 27-session longitudinal study has NOT yet been published. The current study is 9 runs (3x3), not pre-registered, no time-series. However, this blog post itself demonstrates **awareness in the community** that this gap exists and that controlled longitudinal memory evaluation for coding agents needs to be done. The planned study has not appeared in any search results — it is either not published or not indexed.

**METR RCT (July 2025)** — re-confirmed as Rank 3 closest match. Within-subject randomized design on real coding work. Does not evaluate memory.

**ProdCodeBench**
- URL: https://arxiv.org/abs/2604.01527
- Published: April 2026
- Summary: Benchmark from real AI coding assistant sessions (production). Preserves verbatim prompts. Execution-based evaluation.
- Similarity: Real production sessions; outcome-based; realistic task distribution.
- Difference: Not a study of memory systems. No real developer longitudinal tracking. Not pre-registered. Not n=1.

**Anthropic RCT on skill formation (Feb 2026)**
- URL: Reported via InfoQ https://www.infoq.com/news/2026/02/ai-coding-skill-formation/
- Published: February 2026
- Summary: RCT showing 17% lower comprehension in AI-assisted coding; productivity gains not statistically significant.
- Similarity: RCT with real developers, real coding tasks, real outcomes.
- Difference: No memory system. No longitudinal tracking. Not n=1.

### Final synthesis — Iteration 3

After exhaustive search across:
- arxiv (dozens of queries)
- ACL, EMNLP, COLM, CHI, CSCW, MSR, ICSE proceedings 2024–2026
- Papers With Code
- HCI venues
- Industry longitudinal studies (NAV IT, METR, Google, Anthropic, IBM)
- Agent memory system papers (Mem0, Letta, Hindsight, Cognee, LoCoMo, LongMemEval, MemoryArena)
- Copilot/Cursor/Codex deployment studies

**No paper found that combines ALL of:**
1. Real developer(s) doing real coding work
2. Agent memory system actually deployed (Mem0/Letta/Hindsight/Cognee/hand-built)
3. Longitudinal design with >50 real sessions
4. Pre-registered protocol
5. Randomized memory configurations across sessions/worktrees
6. Time-series outcome measurement (task success, time-to-solution, retry count, self-rated quality)

**The closest prior work found:**
- **Stompy blog** (Sandelin): Closest structurally — single codebase, controlled memory conditions, real tasks, outcome metrics — but only 9 runs, not pre-registered, not longitudinal, blog not peer-reviewed, explicitly calls this a pilot with 27-session longitudinal follow-up planned but not published.
- **METR RCT** (Becker et al., 2507.09089): Rigorous within-subject randomized real-developer study. Missing: no memory system, N=16, not n=1.
- **NAV IT Copilot study** (2509.20353): Longitudinal real-developer deployment. Missing: no memory system, N=39, not pre-registered.

---

## Final Verdict: SURVIVED-MY-LANE

**Rationale:** No paper found in the academic literature, industry reports, or grey literature that satisfies the full conjunction of the N1 claim: (1) real coding work, (2) agent memory system deployed and compared, (3) >50 longitudinal sessions, (4) pre-registered protocol, (5) randomized memory configurations, (6) time-series outcome measurement. The Stompy blog post is the only work with partial structural overlap (controlled memory conditions, coding-specific), but it is explicitly an underpowered pilot (n=9 runs), not peer-reviewed, and lacks pre-registration and longitudinal duration. The METR RCT comes closest on methodological rigor (within-subject randomized, real coding tasks, real outcomes) but evaluates general AI tools, not memory systems specifically. The gap between "longitudinal multi-developer AI coding studies" and "single-developer pre-registered memory-system deployment studies" remains wide open.
