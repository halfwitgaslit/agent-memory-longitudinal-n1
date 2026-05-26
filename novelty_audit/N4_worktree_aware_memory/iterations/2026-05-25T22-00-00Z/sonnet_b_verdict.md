# N4 Worktree-Aware Memory — Researcher B Final Verdict

**Verdict: PARTIAL-OVERLAP**

Two real prior art systems found:

1. **Letta Code Context Repositories** (Feb 2026, letta-ai/letta-code): Ships parallel subagents in isolated worktrees that each write memory, then git-merge back to a "main" memory branch. This is the closest prior art — worktree-aware memory with concurrent writes and merge resolution is a shipped production feature.

2. **Engram MCP** (edg-l/engram-mcp and variants): Branch-scoped memory with session handoffs — memory records carry git branch metadata, retrieval is filtered by current branch. Prior art for sequential branch-aware memory, but not parallel/concurrent.

**What survives:** If N4's claim is specifically about controlled parent→child memory injection at worktree fork time, live cross-worktree querying without merge, or fine-grained scope rules (which facts propagate vs. stay isolated), those sub-claims have no identified prior art. Letta's model is fan-out-write-then-merge, not selective live bridging.

**What is killed:** The basic claim that "memory should respect git worktree boundaries" — Letta has shipped this.

**Recommendation:** Narrow N4 to scope-controlled inheritance and cross-worktree querying to distinguish from Letta prior art.
