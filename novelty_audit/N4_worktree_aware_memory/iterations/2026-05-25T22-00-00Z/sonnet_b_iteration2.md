# N4 Worktree-Aware Memory — Researcher B Iteration 2
## Deep characterization of prior art candidates

**Date:** 2026-05-25  
**Researcher:** Sonnet B (industry/OSS lane)

---

## Candidate A: Engram MCP (edg-l/engram-mcp)

**What it does:** MCP server in Rust. Scopes persistent memory to the current git branch. On session end, user runs `engram-cli handoff create` — this captures decisions, blockers, todos on that branch. On resume (possibly on same or different worktree), `engram-cli handoff resume` surfaces the prior session's state. Semantic search via local SQLite + ONNX embeddings.

**Overlap with N4:** HIGH. This is explicitly "branch-aware memory" — memory records carry branch metadata and retrieval is filtered by current branch. The framing is "git branches encode work-in-progress boundaries that prior memory tools ignore."

**Key distinction from N4 claim:** Engram is *single-agent, sequential handoff* — one agent on one branch, pause, resume later. It does NOT address the *parallel multi-worktree* case where multiple concurrent agents share and bridge memory across worktrees. There is no mechanism for a parent agent to inject/share memory into a child worktree agent's context, or for worktree agents to synchronize learned context back to a common memory pool.

---

## Candidate B: Letta Code — Context Repositories (MemFS)

**What it does:** Announced 2026-02-12. Memory is stored as git-tracked files in a local filesystem (MemFS). Multiple concurrent subagents each get isolated worktrees, write memory updates, then merge back via git. Handles conflicts via standard git merge. Memory initialization fans out across N subagents in N worktrees; each processes a slice of history; results merged to main memory branch.

**Overlap with N4:** HIGH. This is the closest prior art. Letta uses worktrees as a concurrency primitive for memory formation — multiple agents write memory in parallel and merge it back. The implementation is specifically worktree-aware.

**Key distinction from N4 claim (pending claim definition from Researcher A):** Letta's worktree memory model is about *concurrent memory formation* (fan-out/merge for speed). The N4 claim — if it's about *selective memory bridging* (sharing specific memories across worktrees while keeping others isolated, or about surfacing cross-worktree patterns for a parent orchestrator) — would be narrower and potentially novel. If N4 is just "memory that respects worktree boundaries," Letta is direct prior art. If N4 adds cross-worktree memory propagation with scope control, Letta only partially overlaps.

**Activated:** Letta Code's `/memfs enable` command, as of early 2026. This is a shipped production feature.

---

## Additional finding: Claude Code issues confirm the gap

Issues #16600 (memory traversal crosses worktree boundaries — bug), #24382 (request for shared auto-memory across worktrees), #39920 (worktrees resolve to main worktree's memory directory — bug). These confirm:
1. Claude Code currently has *accidental* worktree memory bleed (a bug), not intentional bridging.
2. There are competing user desires — some want isolation, some want sharing.
3. No native solution exists in Claude Code.

---

## Iteration 2 Verdict (preliminary)

- N4 is **PARTIALLY KILLED** by Engram (sequential branch-aware handoff) and **substantially overlapped** by Letta Code (parallel worktree memory formation/merge).
- If N4 specifically claims *controlled cross-worktree memory propagation* (parent→child injection, child→parent learning, or selective bridging with scope rules), it may survive as a narrower claim.
- The exact claim definition from Researcher A is needed to finalize.
