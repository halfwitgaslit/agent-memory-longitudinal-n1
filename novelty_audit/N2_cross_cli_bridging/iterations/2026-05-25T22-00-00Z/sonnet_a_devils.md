# N2 Audit — Devil's Advocate Notes (Sonnet A)
**Date:** 2026-05-25T22-00-00Z

## Strongest counter-arguments to SURVIVED verdict

### 1. "Portable Agent Memory" (2605.11032) is very close
The paper proposes MCP tool bindings (`pam_export_memory`, `pam_import_memory`) that are compatible with "Claude, GPT with function calling, Copilot, etc." It uses a format-agnostic JSON/CBOR schema and explicitly notes future "framework adapters." A reviewer could argue this is conceptually identical to the claim and only lacks CLI-specific instantiation.

**Rebuttal:** The paper does not name CLI-specific storage formats (Codex JSONL, Cursor SQLite, Cline JSON), does not provide adapters for them, and its demonstrated scope is LLM-model interop, not coding-assistant-CLI interop. The schema-bridging problem for heterogeneous CLI storage formats is unaddressed.

### 2. Grey-literature tools may count as prior art
Memorix, memory-bridge, agentmemory, and kiro-memory all implement exactly the claimed system, are publicly available on GitHub, and predate any paper submission. If the novelty claim is published in 2026, these could torpedo originality even without a peer-reviewed paper.

**Rebuttal:** These are software artefacts without published claims or evaluation. Academic venues accept novelty claims over prior open-source tools if the paper provides systematic evaluation, protocol formalization, or theoretical analysis. The claim's novelty could rest on formalizing what practitioners built ad-hoc.

### 3. Blackboard architecture is a 40-year-old idea
HEARSAY-II (1970s), HASP, and subsequent blackboard systems all implemented a shared substrate that heterogeneous agents read/write, with schema defined by the blackboard kernel. This is structurally identical to the claim.

**Rebuttal:** Adapting a 1970s architecture to modern CLI-specific binary/JSON/SQLite formats in an MCP-mediated ecosystem is not trivially anticipated by blackboard theory. The novelty is in the concrete schema-bridging layer, not the shared-substrate idea.

### 4. MCP itself is the shared substrate — the claim may reduce to "use MCP"
MCP servers can act as shared memory between any MCP-compatible client. Claude Code, Codex, Cursor, Cline all support MCP. If memory is stored in a shared MCP server, cross-CLI access is MCP's built-in capability.

**Rebuttal:** MCP provides the transport, not the schema translation. The non-trivial contribution is the adapter layer that reads Codex's JSONL rollout format, Claude Code's JSONL with hook-injected metadata, Cursor's SQLite schema, and Cline's JSON conversation cache — and normalizes them. MCP does not solve this; it is merely the delivery mechanism.

## Conclusion
The SURVIVED verdict holds. The paper should acknowledge grey-literature tools explicitly and position against "Portable Agent Memory" (2605.11032) as the closest academic precedent. The key differentiator to emphasize is CLI-specific format heterogeneity and the schema adapter layer.
