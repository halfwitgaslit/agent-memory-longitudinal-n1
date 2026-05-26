# N4 Worktree-Aware Memory — Researcher B Iteration 3
## Final synthesis and verdict

**Date:** 2026-05-25  
**Researcher:** Sonnet B (industry/OSS lane)

---

## Summary of evidence

| System | Feature | Worktree-aware? | Parallel? | Cross-worktree bridging? |
|---|---|---|---|---|
| Engram MCP (edg-l, NickCirv, Gentleman-Programming) | Branch-scoped session handoffs | YES | NO (sequential) | NO |
| Letta Code MemFS / Context Repositories | Git-backed parallel memory formation | YES | YES | YES (merge back to main) |
| Claude Code | Worktree isolation (transcripts/plans) | PARTIAL (bug: memory bleeds) | YES | NO intentional bridging |
| Cursor | Project-level memory | NO | N/A | NO |
| Cline / Roo Code | Session memory, parallel --cwd | NO | NO | NO |
| Mem0 | user/agent/session/app scopes | NO git dimension | YES | NO |
| OpenHands / Devin / Aider | No cross-session memory | NO | NO | NO |
| Anthropic Cowork | Workspace/user scoped memory | NO | NO | NO |
| MCP ecosystem (general) | Various | NO (except engram-mcp) | NO | NO |

---

## Final characterization of prior art

### Engram MCP
Partial prior art for "worktree-aware memory." Scope: single agent, one branch at a time, sequential handoff. Does not handle concurrent multi-worktree scenarios or controlled propagation between parent and child worktrees.

### Letta Code Context Repositories (2026-02-12)
Substantial prior art. Ships: parallel subagents in isolated worktrees, each writes to memory, git-merge resolves conflicts, merged back to a "main" memory branch. This implements worktree-aware memory with concurrent writes and merge-back. **This is the strongest prior art.**

---

## Verdict in my lane

**PARTIAL-OVERLAP**

Rationale: The claim space has significant prior art in Letta Code (MemFS / Context Repositories, Feb 2026) and partial prior art in Engram MCP. However, neither system implements the full pattern if N4 involves:
- Memory selectively *inherited* into a child worktree at spawn time (parent→child injection at fork)
- Fine-grained scope control (which memories are shared vs. isolated per worktree)
- Cross-worktree *querying* without merge (a parent orchestrator reading across multiple live worktrees' memories simultaneously)

Letta's model is fan-out-write then merge-back, not live cross-worktree querying or selective fork-time injection. Engram is sequential-only.

If N4 claims worktree-isolated memory that merges back: **KILLED** (Letta prior art, Feb 2026).  
If N4 claims cross-worktree memory *bridging with scope control* or *live parent-reads across active child worktrees*: **SURVIVED** as a narrower, potentially novel contribution.

The claim needs tighter specification to finalize. Recommend the claim be narrowed to the scope-controlled inheritance/propagation axis to distinguish from Letta.

---

## Key sources

- https://github.com/edg-l/engram-mcp (Engram MCP — branch-aware handoffs)
- https://www.letta.com/blog/context-repositories (Letta Context Repos — Feb 2026)
- https://github.com/letta-ai/letta-code (Letta Code)
- https://github.com/anthropics/claude-code/issues/16600 (Claude Code memory boundary bug)
- https://github.com/anthropics/claude-code/issues/24382 (competing feature requests)
- https://github.com/anthropics/claude-code/issues/39920 (memory resolves to main worktree — bug)
- https://docs.letta.com/letta-code/memfs (MemFS docs)
