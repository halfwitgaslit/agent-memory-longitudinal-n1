# Sonnet B Findings — N1 Longitudinal n=1 Agent-Memory Deployment
Researcher: Sonnet B (Industry/OSS lane)
Audit start: 2026-05-25

---

## Iteration 1 — Findings

**Search scope:** GitHub repos, vendor blogs (Mem0, Letta), Hacker News, academic preprints, Reddit/LocalLLaMA, quantified-self community.

### Top-10 Closest Hits (ranked by similarity to claim)

| Rank | Source | URL | Date | Similarity | Difference |
|------|--------|-----|------|------------|------------|
| 1 | **Mem0 arXiv paper** | https://arxiv.org/abs/2504.19413 | Apr 2025 | Describes production-deployed Mem0 with longitudinal memory extraction across user sessions; 91% lower latency, 90% token savings; cites real user personalization | Paper is vendor-authored, not independent n=1 user study; no behavioral self-assessment of agent; no reflective analysis of what the system learned about the user over time |
| 2 | **Letta (MemGPT) support agent on Discord** | https://www.letta.com/blog/our-next-phase | 2024 | "A support agent that has been learning from Discord interactions for a month" — explicitly longitudinal, real deployment | This is a vendor-run support bot (not solo developer's personal assistant); no published data dump or analysis of memory evolution |
| 3 | **Letta Code memory-first coding agent** | https://github.com/letta-ai/letta-code | 2025 | Designed as "long-lived personal agent" with memory across coding sessions | Product announcement, no published longitudinal study; no user behavioral data published |
| 4 | **HN: "An experiment in separating identity, memory, and tools"** | https://news.ycombinator.com/item?id=46398323 | ~2025 | HN thread title suggests personal experimentation with agent memory architecture | Could not fetch content (rate-limited); unknown if longitudinal or n=1; unknown duration |
| 5 | **Personal.ai platform** | Referenced in search results | 2024–2025 | Commercial platform creating "personal language models" with long-term memory; marketed for individual persistent use | Closed-source commercial product; no published behavioral analysis or self-reflection dataset; vendor not user writes about it |
| 6 | **CloneMem benchmark** | https://arxiv.org/pdf/2601.07023 | Jan 2026 | Benchmarks AI memory over 1–3 years of personal digital traces (diaries, emails, social media) | This is a benchmark/dataset construction paper, not a real-world n=1 deployment; synthetic longitudinal data, not actual agent running on real person |
| 7 | **mnemos-os/mnemos** | https://github.com/mnemos-os/mnemos | ~Dec 2025 | "Production-grade memory operating system…In production use since December 2025" — longitudinal OSS deployment | No evidence of individual n=1 user study; no published analysis; no behavioral data; likely enterprise-oriented |
| 8 | **NirDiamant/Agent_Memory_Techniques** | https://github.com/NirDiamant/Agent_Memory_Techniques | 2025 | 30 runnable notebooks covering Mem0, Letta, MemGPT — educational repo showing how to deploy | Tutorial/demo repo, not a deployed system; no longitudinal data |
| 9 | **OpenNote education platform** | Referenced in Mem0 blog | 2025 | "AI tutors evolved into learning companions that recall past struggles and adapt lessons" after Mem0 integration | B2C product deployment, not solo n=1 study; no published analysis; vendor case study only |
| 10 | **HN "Show HN: self-diagnostic health check for AI agent memory"** | https://news.ycombinator.com/item?id=47170416 | ~2025 | Shows someone built tooling to inspect/maintain agent memory in production | Tooling post, not a longitudinal study; no published behavioral data |

### Summary
No published solo n=1 longitudinal deployment was found where an individual deployed agent memory on themselves, ran it over months, and published behavioral/reflective analysis. The closest artifacts are: (a) vendor-run bots with months of deployment but no user-side analysis, (b) a benchmark simulating 1–3 year personal digital traces (CloneMem), and (c) the HN identity/memory experiment thread (content inaccessible).

---

## Iteration 2 — Findings

**Search scope:** Vendor blogs (Hindsight/Vectorize, Mem0 state-of-2026), Substack personal experiments, LessWrong, Cursor/Aider community, arXiv empirical studies.

### Top-10 Closest Hits (ranked by similarity to claim)

| Rank | Source | URL | Date | Similarity | Difference |
|------|--------|-----|------|------------|------------|
| 1 | **"The Algorithmic Self-Portrait: Deconstructing Memory in ChatGPT"** | https://arxiv.org/abs/2602.01450 | Feb 2026 | Analyzes 2,050 real ChatGPT memory entries from 80 users; finds 96% created unilaterally; GDPR data donations — real-world personal memory, longitudinal use implicit | Multi-participant (n=80), not n=1; not self-deployment study; no behavioral analysis of agent learning evolution; users are data donors not researchers |
| 2 | **OpenClaw on Substack: "I Deployed A Personal AI Agent in less than 15 Minutes"** | https://openclawinstall.substack.com/p/i-deployed-a-personal-ai-agent-in-4bd | 2025 | Solo developer deploys personal AI agent; mentions "persistent memory across sessions"; 1 week of use | 1 week only — not longitudinal; memory system not analyzed; promotional review not scientific; no behavioral data published |
| 3 | **Hindsight (vectorize.io) production deployments** | https://hindsight.vectorize.io | 2025–2026 | "Used in production at Fortune 500 enterprises" with multi-session memory; local Ollama deployment available for individuals | Enterprise focus; no n=1 personal study published; no behavioral data or user analysis available; vendor-authored only |
| 4 | **MultiSessionCollab (arXiv 2601.02702)** | https://arxiv.org/pdf/2601.02702 | Jan 2026 | 19-participant user study with agents across 3 consecutive sessions — memory improves collaboration; participants note personalization | Only 3 sessions, not longitudinal; n=19 not n=1; researcher-designed tasks not naturalistic self-deployment; no long-term behavioral data |
| 5 | **MemNexus / Recallium — Cursor persistent memory** | https://memnexus.ai/blog/2026-02-20-cursor-persistent-memory | Feb 2026 | Products offering account-scoped memory across Cursor sessions; developer-facing personal memory | Product announcement only; no published longitudinal study; no behavioral analysis |
| 6 | **"Enabling Personalized Long-term Interactions…" (arXiv 2510.07925)** | https://arxiv.org/pdf/2510.07925 | Oct 2025 | Position/methods paper on persistent memory + user profiles for LLM agents | No real user data; no deployment; theoretical framework only |
| 7 | **Mem0 state-of-2026 blog** | https://mem0.ai/blog/state-of-ai-agent-memory-2026 | 2026 | Cites benchmarks and changelogs; no individual case studies | Purely vendor-authored; zero independent n=1 citations; no behavioral data |
| 8 | **Nate's Newsletter on Substack (agent memory)** | https://natesnewsletter.substack.com | 2025 | Discusses enterprise memory gap and patterns across 2025 agent deployments | Enterprise/B2B focus; no personal n=1 deployment; synthesis post not primary research |
| 9 | **Cursor "Memory Bank" community posts** | https://forum.cursor.com/t/persistent-ai-memory-for-cursor/145660 | 2025 | Developer community discusses personal persistent memory across Cursor projects | Community feature request/discussion; no longitudinal study; no systematic behavioral data |
| 10 | **"What LLM Agents Do When Left Alone" (arXiv 2509.21224)** | https://arxiv.org/pdf/2509.21224 | Sep 2025 | Studies baseline autonomous agent behavior; reproducible behavioral framework | Lab study not personal deployment; not n=1 user; not memory-focused per se |

### Iteration 2 Summary
Deeper search confirms: no published personal n=1 longitudinal deployment study found. The ChatGPT memory paper (Feb 2026, n=80) is the closest falsifier but fails on n=1 and self-deployment. The Cursor/Hindsight/MemNexus ecosystem shows solo developers using persistent memory but no one has published a behavioral study of what their agent learned about them over months.

---

## Iteration 3 — Findings

**Search scope:** Daniel Miessler's PAI (Personal AI Infrastructure), Mastra user reports, ByteRover personal case studies, quantified-self AI lifelog community, practitioner conference talks.

### Top-10 Closest Hits (ranked by similarity to claim)

| Rank | Source | URL | Date | Similarity | Difference |
|------|--------|-----|------|------------|------------|
| 1 | **Daniel Miessler — "Building Your Own Personal AI Infrastructure"** | https://danielmiessler.com/blog/personal-ai-infrastructure | Jul 2025 (updated Jan/Apr 2026) | **STRONGEST FALSIFIER CANDIDATE.** Solo developer, n=1 deployment of custom memory system (3-tier: Session/Work/Learning Memory) running ~2 years; 3,540 signals captured; 84 rating-1 failure events analyzed to derive behavioral steering rules; "Algorithm" versioned v0.1–v0.2.23; publicly documented reflective learning from behavior; conference talk at [un]prompted 2026 | Uses CUSTOM architecture (not Mem0/Letta/Hindsight/etc.); eventually expanded beyond n=1 to include business partner; behavioral analysis is infrastructure-focused blog post, not academic paper; no IRB/study design; no statistical analysis of longitudinal change |
| 2 | **Mastra user report: "session running for months"** | https://mastra.ai/blog/announcing-mastra-code | 2025 | One Mastra Code user reports "having a session running for months, maintaining useful knowledge without losing what was learned" | Single anecdote in vendor blog, no published data, no behavioral analysis |
| 3 | **Cognitive Revolution podcast: Miessler PAI deep-dive** | https://www.cognitiverevolution.ai/pioneering-pai-how-daniel-miessler-s-personal-ai-infrastructure-activates-human-agency-creativity/ | 2025–2026 | Podcast interview with Miessler on his longitudinal personal AI memory deployment — widely distributed | Podcast interview not academic study; no data tables; no methodology section |
| 4 | **ByteRover: Clawdbot case study** | https://www.byterover.dev/blog/byterover-agent-skill-to-give-clawdbot-moltbot-persistent-context | 2025 | Developer memory case study for a personal AI employee; hierarchical persistent context | Enterprise/product use case, not personal self-study; no longitudinal user data |
| 5 | **Daniel Miessler — self.md profile** | https://self.md/people/daniel-miessler-personal-ai-infrastructure/ | 2025–2026 | Third-party documentation of Miessler's PAI work — confirms longitudinal personal deployment | Summarization of Miessler's own work, not independent replication |
| 6 | **ChatGPT Algorithmic Self-Portrait (arXiv 2602.01450)** | https://arxiv.org/abs/2602.01450 | Feb 2026 | Closest academic paper: n=80 users donate ChatGPT memory data; 96% memories created unilaterally; 28% GDPR-sensitive; analysis of what system learned about users | n=80 not n=1; not self-deployment study; retrospective analysis not prospective longitudinal design |
| 7 | **PersonaMem-v2 (arXiv 2512.06688)** | https://arxiv.org/pdf/2512.06688 | Dec 2025 | Implicit user persona learning via agentic memory; personalized intelligence framework | Simulation/benchmark paper; no real user deployment; no longitudinal data |
| 8 | **ChatBotX: "Personal AI Agent as Daily Operating System 2026"** | https://chatbotx.io/blog/personal-ai-agent-how-to-design-your-own-intelligent-daily-operating-system-in-2026/ | 2026 | Describes agents knowing "Monday morning priorities differ from Friday afternoons" after 2 weeks — behavioral emergence claim | Tutorial/opinion piece; no actual data; no published deployment |
| 9 | **ByteRover arXiv paper** | https://arxiv.org/html/2604.01599v1 | Apr 2026 | Academic paper on ByteRover agent-native memory; LLM-curated hierarchical context | System paper not user study; no n=1 longitudinal personal deployment |
| 10 | **Letta Code app launch** | https://www.letta.com/blog/introducing-the-letta-code-app | Apr 2026 | "Deeply personalized agents that learn over time and work locally on your machine" | Product announcement; no published user behavioral data |

### Iteration 3 Summary
**Critical finding: Daniel Miessler's PAI is the strongest falsifier found.** It is an n=1 personal deployment of a custom multi-tier agent memory system, running ~2 years, with 3,540 signals accumulated, 84 failure events analyzed to derive behavioral steering rules, versioned across v0.1–v0.2.23, publicly documented in a blog post and a conference talk ([un]prompted 2026). This is a real longitudinal n=1 deployment with published reflective analysis. However, it differs from the claim in three ways: (1) uses a custom architecture not a named framework like Mem0/Letta, (2) blog post not academic paper, (3) eventually expanded to multi-agent/multi-person. If the claim is specifically about academic study design + named frameworks, it survives. If the claim is "first published longitudinal n=1 agent-memory self-deployment with behavioral reflection," **Miessler's PAI likely predates or parallels it.**
