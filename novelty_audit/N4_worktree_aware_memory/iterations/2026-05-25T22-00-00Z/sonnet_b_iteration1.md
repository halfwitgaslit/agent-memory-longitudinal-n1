# N4 Worktree-Aware Memory — Researcher B Iteration 1
## Industry / OSS Scan

**Date:** 2026-05-25  
**Researcher:** Sonnet B (industry/OSS lane)  
**Focus:** Do existing industry products or OSS repos already implement worktree-aware memory?

---

### Claude Code itself

GitHub issues #16600 and #39920 both document that Claude Code does NOT correctly scope memory to worktree boundaries — it is a known bug/feature-request that CLAUDE.md traversal reads from both the worktree AND the parent repo directory. Issue #24382 requests the opposite: auto-memory shared across worktrees of the same repo. This confirms: as of mid-2026, Claude Code lacks native worktree-aware memory bridging. The built-in worktree support isolates transcripts/plans per worktree, but memory files are NOT properly scoped.

**Evidence:** https://github.com/anthropics/claude-code/issues/16600  
**Evidence:** https://github.com/anthropics/claude-code/issues/39920

---

### Cursor

No branch-aware or worktree-scoped memory feature found. Cursor's "Memory Bank" is project-level, not branch-level. Background agents work on separate branches but there is no memory partitioning per branch. The Cursor community forum has a feature request for "branch mode" but it is not shipped.

---

### Cline / Roo Code

Cline documents worktree workflows (parallel `--cwd` instances) but has no built-in branch-aware memory. Memory is session-scoped, not branch-scoped.

---

### Engram MCP (edg-l/engram-mcp and NickCirv/engram and Gentleman-Programming/engram)

**SIGNIFICANT OVERLAP FOUND.**  
Multiple "engram" repos exist:
- `edg-l/engram-mcp`: Described as "branch-aware session handoffs, local ONNX embeddings, SQLite-backed semantic search." Explicitly scopes memory to git branches — context from one branch does not leak into another.  
- `Gentleman-Programming/engram`: Go binary, SQLite+FTS5, MCP server, with branch-aware handoffs documented.  
- `NickCirv/engram`: Claims 89% token reduction, live in 8 IDEs.

All three frame "branch-aware" memory as their core differentiator. This is direct prior art for worktree-aware memory scoping.

---

### Letta / Letta Code (Context Repositories)

**SIGNIFICANT OVERLAP FOUND.**  
Letta announced "Context Repositories" on 2026-02-12: git-backed memory where each subagent works in its own git worktree, writes memory, and merges back via standard git operations. Memory initialization, reflection, and defragmentation all run as subagents in isolated worktrees. This is a production system with worktree isolation as a first-class memory primitive.

**Evidence:** https://www.letta.com/blog/context-repositories  
**Evidence:** https://github.com/letta-ai/letta-code

---

### Mem0

Mem0's scoping model uses `user_id`, `agent_id`, `run_id/session_id`, `app_id/org_id` — no git branch or worktree dimension in the schema. No branch-aware memory found.

---

### Anthropic Cowork

Memory is workspace-scoped and user-scoped, not branch/worktree-scoped. No worktree awareness found.

---

### OpenHands / Devin / Copilot Workspace / Aider

OpenHands explicitly calls out session-bounded memory as a limitation — agents rediscover the codebase every session. No branch-aware memory. Devin and Copilot Workspace use branch isolation for parallelism but have no documented worktree-aware memory bridging.

---

### Conclusion for Iteration 1

Two strong prior-art candidates identified:
1. **Engram MCP** — explicitly markets branch-aware session handoffs
2. **Letta Context Repositories** — worktree-isolated memory with git-merge semantics

These must be characterized more precisely in iteration 2.
