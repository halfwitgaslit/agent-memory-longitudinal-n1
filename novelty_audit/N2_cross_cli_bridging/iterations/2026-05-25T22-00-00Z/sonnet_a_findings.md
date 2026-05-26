# N2 Novelty Audit — Academic Findings (Sonnet A, Academic Lane)
**Auditor:** Sonnet A (academic subset)
**Date:** 2026-05-25T22-00-00Z
**Claim:** Cross-CLI memory bridging — memory written in one agentic CLI (e.g., Codex) retrieved and injected into another (e.g., Claude Code) on the same project, requiring schema adapters for CLI-specific formats (Codex JSONL, Claude Code JSONL, Cursor SQLite, Cline JSON, etc.).

---

## Iteration 1: Broad sweep

Searched arxiv for "cross-tool memory", "agent memory portability", "multi-agent memory sharing", "shared memory store agent". Key hits:

| Paper | Venue/Date | Relevance |
|---|---|---|
| "Collaborative Memory: Multi-User Memory Sharing in LLM Agents" (2505.18279) | arxiv May 2025 | Multi-user sharing with access control. No CLI specificity. |
| "Memory as a Service (MaaS)" (2506.22815) | arxiv Jun 2025 | MCP-based shared memory as module. No CLI format bridging. |
| "Multi-Agent Memory from a Computer Architecture Perspective" (2603.10062) | SIGARCH Mar 2026 | Frames shared vs. distributed memory paradigms. Conceptual. No CLI bridging. |
| "INMS: Memory Sharing for Large Language Model based Agents" (2404.09982) | arxiv Apr 2024 | Shared conversational memory pool for abstract multi-agent LLM systems. No specific CLIs. |
| "MemCollab: Cross-Agent Memory Collaboration" (2603.23234) | arxiv Mar 2026 | Cross-agent memory via contrastive trajectory distillation. No CLI specificity. |

**Finding:** None of these address the specific CLI-to-CLI bridging scenario.

---

## Iteration 2: Targeted sweep

Searched "interoperable agent memory", "portable agent memory", "memory transfer agent", and MCP-as-shared-substrate literature.

| Paper | Venue/Date | Relevance |
|---|---|---|
| "Portable Agent Memory" (2605.11032) | arxiv May 2026 | CLOSEST HIT — protocol for cross-model memory portability with Merkle-DAG provenance, JSON/CBOR serialization, MCP tool bindings. **Does NOT address CLI-specific formats (Codex JSONL, Cursor SQLite, Cline JSON, etc.)** and does not name any agentic CLIs as source/target systems. Scope is GPT-4/Claude/Gemini/Llama model interop, not coding-assistant CLIs. |
| "SAMEP: Secure Agent Memory Exchange Protocol" (2507.10562) | arxiv Jul 2025 | Protocol for persistent memory across sessions with MCP/A2A interoperability. No CLI-specific schema bridging. |
| "Enhancing MCP with Context-Aware Server Collaboration" (2601.11595) | arxiv Jan 2026 | Shared Context Store (SCS) for MCP servers. General multi-agent, not CLI-specific. |
| "Survey of Agent Interoperability Protocols" (2505.02279) | arxiv May 2025 | MCP, ACP, A2A, ANP compared. No memory bridging between coding CLIs. |

**Finding:** "Portable Agent Memory" is the closest academic precedent but operates at the LLM-model level (GPT-4↔Claude↔Gemini), not the CLI-tool level. The schema concern (Codex JSONL vs. Cursor SQLite vs. Cline JSON) is entirely absent.

---

## Iteration 3: CLI-specific schema bridging + classical architectures

Searched for CLI-specific cross-agent memory, blackboard architectures in LLM context, FIPA/KQML intellectual predecessors.

**CLI-specific findings (non-academic, grey literature only):**
- `memorix` (GitHub: AVIDS2/memorix) — MCP layer compatible with Cursor, Claude Code, Codex, Windsurf, Gemini CLI. Open-source tool, no peer-reviewed paper.
- `memory-bridge` (GitHub: Bbasche/memory-bridge) — Two-way memory sync between coding agents with format adapters. Open-source, no paper.
- `agentmemory` (GitHub: rohitg00/agentmemory) — Persistent memory for Claude Code, Codex CLI, Cursor, etc. Open-source, no paper.
- `kiro-memory` (GitHub: Auriti-Labs/kiro-memory) — Cross-session memory for Claude Code, Cursor, Windsurf, Cline. Open-source, no paper.
- Blog: "Keeping Claude Code, Codex, and Cursor memory in sync" (coding-with-ai.dev) — practitioner post, no academic venue.
- Mem0 blog: "Codex CLI Memory" — vendor documentation.

**Blackboard architecture hits:**
- "LLM-Based Multi-Agent Blackboard System" (2510.01285, arxiv Oct 2025) — blackboard as shared context, but homogeneous agent population, no cross-CLI schema bridging.
- "Intrinsic Memory Agents: Heterogeneous Multi-Agent LLM Systems" (2508.08997) — heterogeneous agents sharing memory, but no CLI-specific formats.

**FIPA/KQML:**
- Classical precedents (1990s–2000s) exist for agent communication over shared knowledge bases. No direct intellectual lineage to coding CLI memory formats.

---

## Summary of closest misses

1. **"Portable Agent Memory" (2605.11032):** Proposes a cross-agent memory protocol with MCP bindings. Addresses heterogeneous model interop (GPT-4/Claude/Gemini). Future work mentions "framework adapters" without specifics. Does NOT address CLI-specific storage schemas.

2. **Grey-literature tools (memorix, memory-bridge, agentmemory):** These actually implement the exact claim — schema-bridging across CLI-specific formats via MCP. None are peer-reviewed academic papers.

3. **Blackboard/MaaS/MCP papers:** Address shared memory infrastructure conceptually, not CLI-format translation.

---

## Verdict

**SURVIVED** (in academic lane).

No peer-reviewed paper explicitly bridges memory between two or more distinct agentic CLIs while addressing CLI-specific storage format differences. The closest academic work ("Portable Agent Memory") operates at the model-API level and ignores CLI storage schemas. The claim's specific contribution — schema-bridging adapters between Codex JSONL, Claude Code JSONL, Cursor SQLite, and Cline JSON formats — has no academic precedent found.

Grey-literature implementations exist (memorix, memory-bridge, agentmemory) and could constitute prior art in an IP sense, but they are software artefacts, not published academic claims.
