# N4 — Worktree-Aware Memory: Opus Final Verdict
**Date:** 2026-05-25T22-00-00Z
**Auditor:** Opus consolidator (adversarial-to-claim)

---

## 1. Final verdict

**`partial-overlap`** — leaning hard toward `dead-on-arrival` for the headline claim. The basic "worktree-isolated memory that merges back via git" pattern is **shipped production** prior art (Letta Code, Feb 2026). What survives is a narrow technical residue, not a paper-grade contribution.

## 2. Confidence

**High.** All three lanes converge on identical conclusions independently. Letta's `letta-ai/letta-code` Context Repositories blog post (2026-02-12) is unambiguous, dated three months before the audit, and explicitly describes "each subagent works in its own git worktree, writes memory, and merges back via standard git operations." Engram MCP independently markets "branch-aware session handoffs" as its core differentiator. Triangulation from Researcher C's structural-analogue search (Dolt branch-views, AWS AgentCore hierarchical namespaces, OS fork/CoW) confirms the pattern itself is ancient.

## 3. Top 3 closest prior works

### #1 — Letta Code Context Repositories / MemFS (letta-ai, 2026-02-12) — KILL SHOT for headline claim
> "Memory is stored as git-tracked files in a local filesystem (MemFS). Multiple concurrent subagents each get isolated worktrees, write memory updates, then merge back via git. Handles conflicts via standard git merge. Memory initialization fans out across N subagents in N worktrees; each processes a slice of history; results merged to main memory branch." (Researcher B, iteration 2)

**Did NOT do:** (a) selective parent→child memory injection at fork time with scope rules (Letta ships full inheritance, not curated); (b) live cross-worktree querying from a parent orchestrator without merge; (c) fine-grained per-fact propagation policy. Letta's primitive is fan-out-write-then-merge for *concurrent memory formation* — speed, not selective bridging.

### #2 — Engram MCP (edg-l/engram-mcp, Gentleman-Programming/engram, NickCirv/engram)
> "Branch-aware session handoffs, local ONNX embeddings, SQLite-backed semantic search. Explicitly scopes memory to git branches — context from one branch does not leak into another." (Researcher B, iteration 1)

**Did NOT do:** Concurrent multi-worktree fleet (it's single-agent sequential handoff); parent→child propagation; cross-branch querying; the 32-worktree-fleet coordination unit.

### #3 — Git Context Controller (GCC, arxiv 2508.00031, Wu et al. 2026)
> "Elevates agent context to a persistent versioned workspace with explicit COMMIT, BRANCH, MERGE, CONTEXT operations. SOTA on SWE-Bench Verified (>80%)." (Researcher A)

**Did NOT do:** Bind to actual git worktrees — GCC's "branch" is an abstract reasoning branch inside a single agent session, decoupled from the repository's VCS. A trivial extension reviewers will demand we engage with.

**Honorable mentions:** CAID (arxiv 2603.21489) — real worktree fleet, no memory layer. AWS AgentCore Memory — hierarchical namespaces but identity-scoped, not workspace-scoped. Dolt — branch-scoped derived state in the data domain. Cursor 2.0/3.0 `/worktree` — file-context isolation only.

## 4. The exact surviving gap

Letta Code kills the headline. The smallest defensible residue, sub-claim by sub-claim:

| Sub-claim | Status |
|---|---|
| "Memory should respect git worktree boundaries" | **DEAD** (Letta MemFS, Feb 2026) |
| "Parallel subagents write per-worktree memory and git-merge back" | **DEAD** (Letta MemFS, Feb 2026) |
| "Memory records carry branch metadata; retrieval is branch-filtered" | **DEAD** (Engram MCP) |
| "Selective parent→child memory injection at fork time with explicit scope rules (which facts inherit, which don't)" | **ALIVE** — no prior art identified |
| "Live cross-worktree querying without merge (parent orchestrator reads across N concurrent live child worktrees' memories)" | **ALIVE** — Letta is merge-back only, not live cross-read |
| "Fine-grained per-fact propagation policy with empirically-calibrated promotion thresholds (this fact promotes to parent at confidence ≥ X, support ≥ Y)" | **ALIVE** — composes with N3 lifecycle FSM |
| "32-worktree-fleet as the coordination unit with measured outcomes" | **ALIVE empirically** — academic record contains no fleet study at this scale |

The surviving surface is roughly 25–30% of the original claim. It is paper-thin as a standalone contribution and only credible as a *composition* with N1 (longitudinal n=1) and N3 (lifecycle FSM).

## 5. Repositioning recommendation

Abandon "worktree-aware memory" as a standalone novelty claim. **Reposition as: "Selective inheritance and live cross-worktree querying as a policy layer on top of Letta-style MemFS."** Frame Letta's MemFS as the *substrate* and the contribution as the *policy/governance layer* on top: which memories inherit at fork, which propagate at merge, which surface to a parent orchestrator reading across live worktrees. Crucially, fold this into a unified contribution with N3 (lifecycle FSM with empirical calibration) and N1 (longitudinal n=1 evaluation on the 32-worktree fleet), so the paper's contribution is the *governed promotion pipeline across a worktree fleet with empirical evidence*, not "worktree-aware memory" — which is now table stakes.

A secondary repositioning angle: position the work as the **first empirical study of worktree-aware memory in deployment**, treating Letta MemFS as a baseline. The novelty becomes evidentiary, not architectural.

## 6. Falsification-test residual risk

**Medium-high.** Specific risks:
- **Letta documentation depth:** Researcher B did not exhaustively read Letta's MemFS docs at `docs.letta.com/letta-code/memfs`. Letta may already ship policy hooks for selective inheritance — if so, "ALIVE" sub-claims could collapse to DEAD. **Action:** before publication, do a deep technical read of Letta's MemFS API surface, including conflict-resolution hooks, scope predicates, and any plugin/policy SDK.
- **Letta velocity:** Letta is actively shipping (Feb 2026 release in a fast-moving area). Between today (May 2026) and publication, Letta could ship selective inheritance, live cross-worktree queries, or per-fact propagation policies. The narrow residue could be killed mid-review.
- **GCC extension:** A reviewer can argue GCC's COMMIT/BRANCH/MERGE/CONTEXT abstractions trivially extend to real worktrees, eliminating the architectural novelty. Counter requires non-trivial mechanism (policy layer, empirical calibration).
- **Engram roadmap:** Three independent "engram" repos exist — one may already ship cross-branch querying. Researcher B's coverage was surface-level for the non-edg-l forks.
- **Internal Cursor/Devin/Cognition unreleased work:** Closed-source vendors (Cursor 3.0, Cognition/Devin) may have unreleased worktree-aware memory features. Unfalsifiable without insider access; acknowledge as residual uncertainty.

## 7. Per-researcher lane verdicts and resolution

| Lane | Verdict | Key evidence |
|---|---|---|
| A (Academic) | `partial-overlap` | GCC has abstract branch memory without git binding; CAID has worktrees without memory layer |
| B (Industry/OSS) | `partial-overlap` (leaning DOA) | Letta Code MemFS ships the headline claim; Engram MCP ships branch-scoped memory |
| C (Adjacent fields) | `partial-overlap` | Pattern is ancient (OS fork, Dolt, AgentCore); specific composition novel |

**Resolution:** No disagreement on verdict label. All three lanes returned `partial-overlap`. However, the *weight* of Lane B's findings — Letta as a shipped Feb 2026 production system — should reframe the headline. Lane A's academic gap (no paper has done this) is far less defensible when the industry has already shipped it three months ago: NeurIPS/ICLR reviewers will treat Letta as prior art regardless of whether it appeared in arxiv. Final verdict honors Lane B as the dominant signal and downgrades the headline claim accordingly.

## 8. Single-paragraph reviewer-grade summary

**N4 ("worktree-aware memory") cannot stand as headlined.** Letta Code's Context Repositories / MemFS, publicly released 2026-02-12, ships precisely the claimed primitive: per-subagent isolated git worktrees, in-worktree memory writes, and git-merge propagation back to a main memory branch — production code in `letta-ai/letta-code` with public blog and docs. Engram MCP independently markets branch-scoped memory with session handoffs. The structural pattern (parent state, divergent children, optional merge) is otherwise ancient — OS fork/CoW, Dolt branch-views, Helm overlays, AWS AgentCore hierarchical namespaces. What remains defensible is narrow: selective parent→child injection at fork with explicit scope rules, live cross-worktree querying without merge, and empirically-calibrated per-fact promotion policy across a worktree fleet. None of these survive as a standalone contribution; the only credible repositioning is to fold them into a unified contribution with N1 (longitudinal n=1) and N3 (rule-lifecycle FSM) — a *governed promotion pipeline atop a MemFS-like substrate, evaluated empirically on a 32-worktree fleet*. The architectural novelty is gone; the contribution must become evidentiary or governance-layered.
