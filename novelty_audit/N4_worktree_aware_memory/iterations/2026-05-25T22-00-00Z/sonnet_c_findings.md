# N4 Worktree-Aware Memory — Researcher C (Adjacent Fields)
# Iteration: 2026-05-25T22-00-00Z

## Scope
Adjacent fields: VCS internals, DB branching, config hierarchy, OS CoW, distributed state, notebook branching, multi-tenant scoping.

---

## Iteration 1 — Structural Analogues to Parent+Override Scoped State

### VCS internals
- **Git worktrees**: isolated working directory + index sharing one object store. No notion of "branch-aware knowledge" stored by git itself beyond commits and refs. State is structural (file tree), not semantic (agent memory/knowledge).
- **Mercurial/Sapling**: bookmarks track branch tips in metadata files (Sapling uses MetaLog for atomicity). No per-branch derived semantic knowledge — only commit graph position.
- **Dolt (git for data)**: branches isolate full DB state. Views are versioned per-branch via `dolt_schemas`. This is the closest structural analogue: branch-scoped derived state (views) that inherits from (and can diverge from) the main branch schema. **Partial overlap with N4 structurally**, but the domain is data/SQL, not agent memory.

### DB cloning
- **Snowflake zero-copy clones**: CoW snapshot of table/schema/DB state. Clones diverge independently. No concept of re-merging derived knowledge back to parent. Structural, not semantic.
- **Neon**: branch-per-PR database state; same structural pattern.

### Config hierarchy
- **Helm/Kustomize/Argo CD**: parent values.yaml + branch/env overlays. Hierarchical override is foundational. No per-worktree dynamic knowledge — static config only.
- **ESLint**: flat config with file-glob overrides. No branch-specific overlay mechanism exists natively.

---

## Iteration 2 — Agent-Space Prior Art for Worktree-Scoped Memory

### Cursor 2.0/3.0 (Oct 2025 / Apr 2026)
- Native multi-agent with up to 8 concurrent agents in isolated git worktrees.
- `/worktree` command for branch-isolated task sandboxing.
- **Key gap**: isolation of *file context* per worktree, not isolation of *semantic agent memory*. Each agent gets its own working directory; there is no described mechanism for per-worktree memory stores that inherit from a shared parent memory and merge back.

### Augment Code, agent-worktree (nekocode/agent-worktree)
- Workflow tooling for running agents in parallel git worktrees.
- Focus: preventing file conflicts, lock contention.
- No evidence of per-worktree *memory namespacing* that inherits parent knowledge.

### Amazon Bedrock AgentCore Memory (2025-2026)
- Hierarchical namespaces: org → app → user → session → run.
- Supports hierarchical retrieval (query at any level).
- **Partial overlap**: this is scoped memory with parent-child inheritance — the same structural pattern as N4.
- **Key gap**: namespace hierarchy is identity-based (org/user/session), NOT workspace/branch-based. No concept of a "git worktree" as a memory scope dimension.

### mem0 / State of AI Agent Memory 2026 report
- Multi-scope memory tags: user_id, agent_id, run_id, session_id, org_id.
- No branch/worktree dimension mentioned.

---

## Iteration 3 — Structural Pattern Universality vs. Agent-Space Novelty

### OS fork + CoW
- The parent→child state inheritance + divergence pattern is literally the foundational OS primitive (fork/CoW). Children inherit full parent state; writes diverge. No merge path back to parent by default.
- This is the *oldest* instance of the pattern. N4 is a semantic/application-layer instantiation of it.

### CRDTs / Vector Clocks
- Distributed systems handle concurrent branching state + merge via CRDTs and vector clocks.
- N4 would need merge semantics to be non-trivial. If worktree memories just diverge and never merge, this is simpler (fork without reconciliation).

### Narrative/game-state branching
- Save-game divergence, branching narrative (e.g., visual novels, Ink language) — branch state from a checkpoint, diverge, optionally converge. Same pattern. Domain-specific, not agent memory.

### Multi-tenant SaaS
- Org → team → user → session scoping is universal. AWS AgentCore Memory brings this directly to agents (see Iteration 2).

---

## Verdict

**PARTIAL-OVERLAP**

The parent+override scoped state pattern is ancient and universal (OS fork, Helm overlays, Dolt branch-views, AWS AgentCore namespaces). The *structural* pattern is not novel.

**What survives in the agent space specifically:**
The combination of (a) git worktree as the *scoping key* for agent memory, (b) inheritance from a shared parent memory at worktree creation, and (c) optional merge/promotion of branch-memory back to parent on task completion — this *specific three-part composition* applied to agent memory has no identified prior art.

Current tooling (Cursor, Augment, agent-worktree) isolates file *workspace* per worktree but treats agent memory as either global or session-scoped without worktree awareness. AWS AgentCore uses hierarchical namespaces but they are identity-scoped (user/session), not workspace/branch-scoped. Dolt has branch-scoped derived state but in the data domain, not agent knowledge.

**The novelty is narrow but real**: git-worktree as a first-class dimension of agent memory scoping, with inheritance and merge semantics, is not present in any surveyed system. The broader structural pattern is not novel; the specific application to git-worktree-aware agent memory in the agentic coding context is.
