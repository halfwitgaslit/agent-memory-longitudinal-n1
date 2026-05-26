# N4 — Worktree-Aware Memory: Academic Falsification Audit
**Researcher:** Sonnet A (academic lane)
**Date:** 2026-05-25T22-00-00Z
**Verdict-in-lane:** PARTIAL-OVERLAP

---

## Closest Hits

### 1. Git Context Controller (GCC) — arxiv 2508.00031 (Wu et al., March 2026)
**Overlap level: HIGH on structure, LOW on the specific claim.**
GCC elevates agent context to a persistent versioned workspace with explicit COMMIT, BRANCH, MERGE, CONTEXT operations. Agents can branch reasoning paths, checkpoint milestones, and merge trajectories. This is the closest structural analogue. However, GCC's "branch" is an *abstract reasoning branch inside a single agent session* — it is not keyed to a git worktree or a VCS branch in the actual repository the agent operates on. There is no concept of: "this worktree inherits parent-branch memory; its own learnings stay isolated until the branch merges." SOTA on SWE-Bench Verified (>80%).

### 2. CAID — arxiv 2603.21489 (Geng & Neubig, CMU, March 2026)
**Overlap level: MEDIUM on mechanism, LOW on memory inheritance.**
Centralized Asynchronous Isolated Delegation creates isolated git worktrees per agent for code execution isolation. This is the use case (multi-agent fleet, parallel worktrees). However, the isolation is *workspace isolation* (no file-system conflicts), not *memory scoping*. There is no published mechanism for memory inheritance from parent-branch prior learnings. Each agent gets a clean worktree; accumulated knowledge is not propagated downward or upward through branch lineage.

### 3. AgentGit — arxiv 2511.00628 (Li et al., Nov 2025)
**Overlap level: LOW.**
Git-like rollback and branching for multi-agent LangGraph pipelines. Supports state commit/revert/branch for error recovery and parallel trajectory exploration. Memory is checkpointed agent state, not structured per git-branch; no notion of branch-lineage memory inheritance.

### 4. Empirical Study of Multi-Agent Collaboration — arxiv 2603.29632 (March 2026)
**Overlap level: LOW.**
Uses git worktree isolation + explicit global memory as a testbed instrument to control for contamination. The global memory is a shared flat store, not branch-scoped. Worktrees are isolation units for the experiment, not carriers of lineage-aware memory.

---

## Gaps Not Found in Literature

After three rounds of search across:
- arxiv branch-aware / worktree-aware memory queries
- IDE agent papers (Copilot Workspace, Devin, SWE-agent)
- Multi-agent fleet + memory isolation papers
- Agent memory surveys (2603.07670, 2602.19320, 2512.13564)
- AgentGit, CAID, GCC, CAT, A-Mem, MIRIX, Lore

**No paper found that:**
1. Keys memory scope to a specific git branch/worktree identity
2. Implements parent-branch memory inheritance at worktree creation time
3. Keeps per-worktree learnings isolated until branch merge propagates them upward
4. Targets a fleet of N worktrees (N=32 or otherwise) as the coordination unit

---

## Verdict: PARTIAL-OVERLAP

The claim survives academically. GCC and CAID bracket the claim from two sides — GCC has the memory-branching abstraction without real git coupling; CAID has the real git worktree fleet without the memory inheritance layer. The combination (git-worktree identity as memory scope key + parent-branch accumulation inheritance + post-merge propagation) is not present in any paper found. The 32-worktree-fleet framing is entirely novel in the academic record.

**Risk level to novelty:** Moderate. GCC in particular could be extended to real git worktrees trivially; reviewers may note this. The novel contribution must be clearly scoped to the *git-branch-as-memory-scope-key* binding and the *inheritance at fork / isolation until merge* lifecycle, not just "branching memory exists."
