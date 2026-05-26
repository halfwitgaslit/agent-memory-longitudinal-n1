# Phase 0 — Novelty Audit Synthesis

**Date:** 2026-05-25
**Inputs:** 4 candidate novelty claims (N1-N4), each audited by 3 parallel Sonnet researchers (academic / industry-OSS / adjacent-fields), each issued a final verdict by an independent Opus consolidator playing PhD-grade adversarial reviewer.

**Total cost so far:** ~$5-10 in agent tokens, ~2 hours wall-clock parallel.

## Final verdicts at a glance

| Claim | Verdict | Confidence | Single strongest killer |
|---|---|---|---|
| **N1** — Longitudinal n=1 agent-memory deployment | `partial-overlap` | high | Daniel Miessler's "Personal AI Infrastructure" (2-year n=1, 3,540 signals, 84 failure events, [un]prompted 2026 talk) + SCED/N-of-1 methodology |
| **N2** — Cross-CLI memory bridging | **`dead-on-arrival`** | high | Mem0's official Claude Code + Codex integrations (docs.mem0.ai); plus Memorix, memory-bridge, AGENTS.md standard, Letta Code |
| **N3** — Rule-lifecycle FSM with empirically calibrated decay | `partial-overlap` | high | Anki's FSRS (fits 21 per-user decay params via gradient descent on 700M reviews); ISO 15489 owns lifecycle FSM; MACLA owns calibrated multi-factor utility in agent memory |
| **N4** — Worktree-aware memory | `partial-overlap` (leaning DOA) | high | Letta Code Context Repositories (`letta-ai/letta-code`, Feb 2026) — ships per-subagent isolated git worktrees + in-worktree memory writes + git-merge back. Engram MCP secondary. |

**Net:** N2 is dead. N1, N3, N4 survive only with sharper framing.

## The common pattern (the actually important finding)

**The architecture is owned. The empirical evaluation on real n=1 longitudinal coding-CLI data is not.**

Across all three surviving claims, the same diagnosis appears:
- Someone else has the architectural primitive (FSRS for decay, ISO 15489 for FSM, Letta Code for worktree-isolated memory, blackboard for cross-tool bridging)
- Nobody has run a rigorous longitudinal n=1 study deploying these primitives against a single developer's real coding work
- The contribution we can defend is **evidence**, not **architecture**

This converges on a single coherent paper, not three separate ones.

## Recommended unified contribution

**Working title:** *"Pre-Registered N-of-1 Longitudinal Evaluation of Agent-Memory Frameworks on a Coding-CLI Substrate"*

**One-paragraph framing (PhD-grade, defensible):**

> Agent-memory systems (Mem0, Letta, Hindsight, Cognee) and their architectural primitives (calibrated decay [cf. FSRS], lifecycle FSMs [cf. ISO 15489], worktree-isolated stores [cf. Letta Code]) have proliferated rapidly with self-reported leaderboard gains, but no rigorous longitudinal n=1 deployment study has measured their actual utility for a single developer's real coding work. We adapt Single-Case Experimental Design (Kazdin 2011; Kratochwill 2010) and N-of-1 trial methodology (Guyatt 1986; CONSORT N-of-1 2015) — specifically the no-washout / interrupted-time-series variant, since memory effects are irreversible — to evaluate four agent-memory configurations against a baseline on one developer's 6-week roomd workflow across 678 prior multi-CLI sessions. Three secondary methodological contributions: (a) per-deployment calibration of decay parameters from agent-task-success signals (extending FSRS to multi-dimensional agent signals); (b) a governance pipeline for cross-worktree memory propagation (extending Letta Code's filesystem-isolation with semantic-promotion rules); (c) reproducibility-grade methods reporting following the EvalCards / HONEST-Mem 15-field protocol.

**Why this survives all 4 Opus verdicts simultaneously:**
- N1's surviving slice (pre-registered randomized multi-framework on coding-CLI with irreversibility-adapted N-of-1) → the design itself
- N3's surviving slice (per-deployment calibrated decay with multi-dimensional task-success signal) → methodological contribution (a)
- N4's surviving slice (governed propagation pipeline + empirical eval on 32-worktree fleet) → methodological contribution (b)
- N2 (cross-CLI bridging) drops entirely → we USE Mem0's existing Claude+Codex integrations rather than claim bridging novelty

## Required citations the paper MUST contain in paragraph one

Per the Opus reviewers — failure to cite these = desk rejection:
1. **Daniel Miessler "Personal AI Infrastructure"** (2025-2026 longitudinal n=1 personal-AI deployment) — strongest practitioner prior art
2. **Kazdin 2011 + Kratochwill 2010** (SCED methodology) — strongest methodology prior art
3. **Guyatt 1986 + CONSORT N-of-1 2015** (n=1 trial standards) — methodology
4. **FSRS algorithm + Anki research** — owns calibrated decay
5. **ISO 15489** — owns records-management lifecycle FSM
6. **Letta Code Context Repositories** (Feb 2026, `letta-ai/letta-code`) — owns worktree-isolated memory
7. **Engram MCP** — owns branch-scoped memory
8. **MACLA (arxiv 2512.18950)** — owns calibrated multi-factor utility in agent memory
9. **GCC (arxiv 2508.00031)** — owns memory branching abstraction
10. **CAID (arxiv 2603.21489)** — owns isolated git worktrees per agent in SWE fleets
11. **Mem0's Claude Code + Codex integration blogs** — owns cross-CLI substrate
12. **Memorix, memory-bridge, AGENTS.md standard** — owns cross-CLI bridging at the application layer

## Falsification-test residual risk (what could still kill us post-publication)

- A workshop paper from a memory-system vendor that gets published in the next 4-8 weeks with a longitudinal eval (this is the highest external risk; multiple vendors flagged "real-world studies" as a roadmap item)
- The "Sandelin" planned 27-session follow-up (flagged by N1-A) — if it ships first, our novelty thins
- Unindexed corporate research (Anthropic / OpenAI / Google internal deployment studies that exist but aren't published)
- A re-categorization of Miessler's work as "already a longitudinal n=1 study" — if a reviewer cites Miessler's [un]prompted 2026 talk as full prior art, our novelty narrows further
- METR's revised methodology (Feb 2026 abandonment of their 57-developer RCT) — if METR ships a new design within our timeline, we may be scooped on the methods side

## Recommended target venues (re-verified against E3 research)

Per E3 consolidated + Opus verdicts, the realistic targets:

| Venue | Deadline | Fit | Notes |
|---|---|---|---|
| **NeurIPS 2026 Datasets & Benchmarks** | typically May (PASSED for 2026) — target 2027 | Highest fit if dataset is the contribution | Requires Croissant metadata + reproduction package |
| **NeurIPS 2026 Workshop papers** | typically Sep-Oct deadlines for Dec workshops | High fit (MemAgents successor if it exists) | Workshop proposal deadline already passed (Jun 6) so this depends on which workshops are approved |
| **ICLR 2027 main track** | ~Sep-Oct 2026 | Highest fit if methodology + dataset + system + empirical results | ~4-5 months out — realistic given Phase 1+2+3 timeline |
| **COLM 2027** | ~Mar 2027 | High fit | ~10 months out — most relaxed timeline |
| **arXiv pre-print** | rolling | Locks priority | Recommended immediately upon submission to any venue |
| **EMNLP 2027 / ACL 2027** | ~Jan/Feb 2027 | Medium fit (more NLP-flavored than agent-systems) | Backup option |

**Recommended primary target:** ICLR 2027 main track. Realistic timeline (Sep-Oct 2026 deadline), strong venue for agent-memory systems work, accepts methodology+system+dataset combinations.

## Go/no-go decision points

### Decision 1: Proceed to Phase 1?

The Phase 0 audit concludes that:
- A defensible PhD-grade contribution **does exist** in the conjunction of (n=1 longitudinal + coding-CLI substrate + per-deployment calibration + governed cross-worktree propagation)
- The contribution is **evidentiary**, not architectural — we use Mem0/Letta/etc. as substrate
- The required citations are extensive but manageable
- The closest competing prior art is **practitioner work + adjacent-field methodology**, not academic agent-memory work — meaning we have a clear methodological-rigor differentiator

**Recommendation:** GO on Phase 1 (foundation substrate build, ~5-10 days, ~$50-150 spend).

If owner declines: HMA-1 (the audit paper) remains as a viable fallback — 70% complete on disk, finishable in ~2 hours / $50.

### Decision 2: Adopt the unified contribution framing?

The 4 verdicts unanimously point toward folding multiple claims into a single empirical study rather than 3 separate papers. This:
- Reduces submission risk (one paper not three)
- Strengthens the contribution (more evidence per claim)
- Lowers external scooping risk (a single integrated submission is harder to scoop than three separate ones)
- Matches the underlying truth of what we'd actually build

**Recommendation:** Adopt the unified "Pre-Registered N-of-1 Longitudinal Evaluation" framing as the working title and contribution scope.

### Decision 3: Cite Miessler in paragraph 1?

The N1 Opus was explicit: "Without these moves the paper is desk-rejectable." The required citation isn't optional.

**Recommendation:** Yes. Treat all 12 required citations as mandatory.

## Owner sign-off needed before Phase 1 starts

- [ ] **Adopt the unified contribution framing** (Pre-Registered N-of-1 Longitudinal Evaluation of Agent-Memory Frameworks on a Coding-CLI Substrate)
- [ ] **Authorize Phase 1 build** (5-10 days, est. $50-150 spend, mostly free self-hosted on M4 Max)
- [ ] **Confirm target venue** (recommended: ICLR 2027 main track, Sep-Oct 2026 deadline)
- [ ] **Accept that Phase 2 deployment is 4-6 weeks of your own real roomd work** (n=1 means YOU are the subject; your daily work IS the experimental unit)

## What's in `current/` for each topic

`distillation/phd/novelty_audit/<N#>_<slug>/iterations/2026-05-25T22-00-00Z/opus_verdict.md` is the canonical verdict for each claim. The full researcher findings are alongside.
