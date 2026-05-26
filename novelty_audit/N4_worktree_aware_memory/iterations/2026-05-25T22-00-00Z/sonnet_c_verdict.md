# N4 Worktree-Aware Memory — Researcher C Verdict
# 2026-05-25T22-00-00Z

VERDICT: PARTIAL-OVERLAP

The structural pattern (scoped state inheriting from a shared parent, diverging, optionally merging) is ancient and appears in:
- OS fork/CoW (universal)
- Dolt per-branch views (data domain)
- AWS AgentCore Memory hierarchical namespaces (agent domain, identity-scoped)
- Snowflake zero-copy clones (data domain)
- Helm/Kustomize config overlays (infra domain)
- Cursor/Augment worktree isolation (agent domain, file-workspace-only)

None of the above apply git-worktree as the scoping key for *semantic agent memory* with inheritance + optional merge-back. The specific composition is not found in surveyed prior art. N4 SURVIVES as a narrow novelty claim within the agent-memory space, provided the claim is precisely scoped to: git-worktree as memory namespace key + parent-memory inheritance + branch-memory merge semantics.
