# Sonnet A — Devil's Advocate
**Audit target:** N1 — Longitudinal n=1 agent-memory deployment  
**Researcher role:** Academic literature (adversarial stance)  
**Date:** 2026-05-25

---

## Iteration 1 — Devil's Advocate

### (1) Did I miss obvious terminology?

Possibly. The claim maps onto "N-of-1" (medicine), "single-subject design" or "single-case design" (behavioral science), "within-person" studies, "experience sampling methodology," and "idiographic methods." None of these terms surfaced agent-memory-specific hits. I also tried "in-the-wild," "field study," and "deployment study" — all dry for agent memory + coding. If there is a hidden body of work, it would be in HCI or behavioral science using these terms without being indexed on arxiv.

Missing terminology I should probe: "personalized agent evaluation," "ecological momentary assessment" + AI, "intensive longitudinal design" + LLM.

### (2) Are there fields I'm not searching?

- **Quantified self / personal informatics literature**: Researchers in this area routinely do n=1 longitudinal tracking of their own productivity tools. There may be blog posts or grey literature (GitHub, personal websites, Substack) rather than peer-reviewed papers — which would constitute prior art for novelty but might not be the "most cited" prior work.
- **Behavioral science / experimental psychology**: Single-subject designs (ABAB reversal, multiple-baseline) are standard here. None found applied to LLM agent memory.
- **Education technology**: Intelligent tutoring system literature has longitudinal student-specific evaluation studies. No overlap found with agent memory systems.

### (3) What would the most-cited closest paper look like?

It would be a CHI or CSCW paper where a researcher deployed an LLM agent with memory for their own work over 3–6 months, tracked outcomes via diary study or automated logging, and published the protocol and results. It would NOT be on arxiv — it would be behind ACM DL. The authors might frame it as a "technology probe" or "autobiographical design" study. No such paper surfaced in my searches.

### (4) HANDOFF flags

**HANDOFF to N2 (industry/OSS):** Check whether Mem0, Letta, or Cognee have published internal user studies, blog posts, or case studies where a single developer tracked memory-on vs memory-off outcomes over weeks. The Sandelin blog (Stompy) is the closest thing I found — N2 should check whether this blog author published the planned 27-session longitudinal follow-up anywhere.

**HANDOFF to N2 (OSS):** Check GitHub for any "memory experiment" repos where a developer logged >50 sessions of coding with agent memory on/off. This would be grey literature prior art.

**HANDOFF to N3 (adjacent fields):** Check quantified self / personal informatics literature for single-subject longitudinal productivity tracking studies. Also check education technology (intelligent tutoring, spaced repetition) for single-learner memory-system evaluation studies. These are structurally very similar to the N1 claim even if the domain differs.

**HANDOFF to N3 (adjacent fields):** Check "autobiographical design" methodology in HCI — self-study designs where HCI researchers use themselves as subjects over months. This is a known HCI method that would map directly onto the N1 claim if applied to agent memory.

---

## Iteration 2 — Devil's Advocate

### (1) Did I miss obvious terminology?

Additional terms I should have tried earlier: "longitudinal diary study" + AI assistant coding, "experience sampling" + LLM agent, "technology probe" + memory + coding agent, "autobiographical design" + AI memory. I ran several of these in Iteration 2 but did not find targeted results. The CSCW/CHI corpora may have buried papers not well-indexed by general web search.

Missing field: **"personal science"** — the emerging discipline of rigorous n=1 self-experimentation. The Personal Science movement has produced methodology papers and some tooling but has not yet intersected LLM agent memory deployment as far as I can tell.

### (2) Are there fields I'm not searching?

I have not directly searched:
- ACM DL directly for CSCW 2024–2025 papers on AI memory + single user
- IEEE Xplore directly for ICSE/FSE/MSR papers on agent memory + longitudinal + individual developer
- Google Scholar directly (my WebSearch queries may not match GScholar's ranking)

I relied on web search to surface ACL Anthology papers — I did not directly search the ACL Anthology search interface, which might surface different results.

### (3) What would the most-cited closest paper look like?

An Organizational Behavior or Human Factors paper measuring individual worker productivity with AI assistance over multiple weeks, using experience sampling methodology and modeling individual-level trajectories. No such paper found in my search.

### (4) HANDOFF flags

**HANDOFF to N2 (industry):** The Mem0.ai "State of AI Agent Memory 2026" blog post (mem0.ai/blog/state-of-ai-agent-memory-2026) explicitly identifies "lack of real-world user studies" as a production gap. If this gap is acknowledged by industry, the N1 claim may be genuinely novel.

**HANDOFF to N3 (adjacent fields):** Check whether the "N-of-1 trial" medical literature (crossover trials in clinical medicine applied to individual patients) has been adapted to software engineering or productivity research. This is a known methodology that has not been applied to AI memory evaluation as far as I can tell.

---

## Iteration 3 — Devil's Advocate

### (1) Did I miss obvious terminology?

The most dangerous terminology gap is **"personal AI"** + longitudinal. PI (personal informatics) literature uses self-tracking methodologies that are structurally n=1. I searched this partially but ACM DL's full proceedings are not available via web search. The 5-day pilot user study in arxiv:2510.07925 is the closest real-user deployment of agent memory found — but 5 days is far short of the claim's weeks/months threshold.

Another gap: **"autoethnography"** applied to AI tools. Autoethnographic studies in HCI involve a researcher systematically documenting their own experience with a technology. This method is rarely indexed on arxiv. If any HCI researcher published an autoethnographic study of LLM agent memory for their own coding work, I would not find it via my search strategy.

### (2) Are there fields I'm not searching?

- **Preprint servers other than arxiv**: SSRN (used for management/organizational behavior papers) may have longitudinal AI productivity studies not indexed on arxiv.
- **Conference workshops and symposia**: CHI/CSCW workshops often host more exploratory work. Not indexed.
- **Theses and dissertations**: PhD dissertations may contain early-stage n=1 longitudinal studies. Not indexed by my search tools.
- **Private repos and technical blogs**: Developers doing self-experiments with Mem0/Letta may have documented results on personal blogs or GitHub without publishing formally.

### (3) What would the most-cited closest paper look like?

Given the recency of both agent memory systems (Mem0, Letta, Hindsight all 2024+) and the rigorous developer productivity measurement methodology (METR RCT, 2025), the would-be most-cited prior art does not have time to exist yet at high citation count. The field is too new. A 2025 paper with 5–20 citations would be the maximum.

The Sandelin blog post (Stompy "first controlled benchmark") is probably the highest-overlap existing work, and it is explicitly positioned as a pilot for a study that has not yet been published. This is practically a **public announcement that the full study does not yet exist**.

### (4) HANDOFF flags

**HANDOFF to N2 (industry/OSS):** Verify that Sandelin's planned 27-session longitudinal study has not been published anywhere. Search "Sandelin" + "Stompy" + "memory" + "longitudinal" on GitHub, Medium, Substack, Twitter/X.

**HANDOFF to N2 (OSS):** Check whether any OSS project (letta-ai/letta, mem0ai/mem0, topoteretes/cognee) has a documented case study from a single developer tracking outcomes across >50 sessions. Issue trackers and discussions may contain informal longitudinal experiments.

**HANDOFF to N3 (adjacent fields):** The METR "Changing Design" blog (Feb 2026) explicitly acknowledges the difficulty of measuring AI coding productivity. This should be cited as evidence that the rigorous longitudinal within-person methodology the N1 claim proposes has NOT been successfully applied even to general AI coding tools, let alone to agent memory systems specifically. This is favorable prior-art evidence for novelty.

**HANDOFF to Opus consolidator:** The Stompy blog post constitutes grey-literature prior art for the concept of controlled memory evaluation in coding agents, but NOT for the full N1 claim (pre-registration, randomized configurations, >50 sessions, time-series). The METR RCT (2507.09089) constitutes prior art for rigorous within-person randomized study design on real coding tasks but NOT for agent memory. The conjunction of these two methodological streams has not been achieved anywhere.
