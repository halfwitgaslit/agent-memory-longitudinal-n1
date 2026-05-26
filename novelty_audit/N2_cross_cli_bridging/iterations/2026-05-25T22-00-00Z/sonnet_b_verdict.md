# Sonnet B Verdict — N2: Cross-CLI Memory Bridging
# Date: 2026-05-25T22:00:00Z
# Lane: Industry / OSS

## Verdict: KILLED

The N2 novelty claim does not survive. Cross-CLI memory bridging between agentic coding
CLIs is already a populated, well-documented space with multiple shipped products and OSS repos.

---

## Strongest Prior Art (rank-ordered by specificity)

1. **Memorix (AVIDS2/memorix)** — the most direct kill. Explicit "cross-agent memory layer via
   MCP" supporting Cursor, Claude Code, Codex, Windsurf, Gemini CLI, GitHub Copilot, Kiro,
   OpenCode, Antigravity, Trae. Has adapter code, knowledge graph, workspace sync.

2. **Mem0** — official product with documented Claude Code AND Codex integrations. Memory scoped
   to user_id; same store surfaces across both tools. Composio integration pages for both.

3. **memory-bridge (Bbasche)** — explicit two-way sync between Claude Code and Codex with
   project-namespaced journal files.

4. **memsearch (zilliztech)** — shared Milvus + Markdown memory format across Claude Code,
   Codex CLI, and other agents.

5. **codex-agent-mem** — portable MCP memory layer for Codex CLI/Desktop, Claude Code, Gemini CLI.

6. **Hindsight** — published guide for Claude Code + OpenClaw sharing same memory bank.

7. **agentmemory**, **mcp-memory-service**, **ai-memory MCP**, **Pieces MCP**, **Memory Bank
   MCP**, **obsidian-second-brain**, **obsidian-mind** — all offer multi-CLI memory sharing
   with adapter code or MCP protocol.

8. **Show HN: OpenTimelineEngine** — HN post explicitly about shared local memory for
   Claude Code and Codex.

---

## Does MCP Itself Count as Cross-CLI Memory Bridging?

**Argument YES (MCP = bridging):**
- MCP is a protocol-level standard. Any MCP memory server (e.g., mcp-memory-service,
  codex-agent-mem, Memorix) that is simultaneously configured in Claude Code and Codex
  is, by definition, a cross-CLI memory bridge. The protocol provides the shared transport;
  the memory server provides the shared store. The N2 claim is solved by MCP's core design.
- Codex can itself run as an MCP server, and Claude can call into it — this is bidirectional
  cross-CLI memory sharing at the protocol level, not just the application level.
- From this angle, N2 is not novel because it reduces to "use MCP," and MCP memory servers
  predate the claim.

**Argument NO (MCP ≠ automatic bridging):**
- MCP is infrastructure; cross-CLI bridging is an application-layer concern. Simply having
  both tools support MCP does not mean they share memory by default — each CLI needs
  explicit configuration pointing at the same server.
- The interesting novelty would be automatic discovery, identity federation, or semantic
  reconciliation of memories written by different agents (e.g., resolving conflicts when
  Claude Code and Codex each update the same fact). MCP provides none of that.
- Existing products (Memorix, Mem0, memory-bridge) all still require manual adapter
  configuration per CLI. A truly novel claim would be zero-config cross-CLI bridging
  with conflict resolution.

**Conclusion:** Even if MCP alone doesn't fully count, the application-layer implementations
(Memorix, Mem0, memory-bridge, memsearch) already exist and explicitly demonstrate the N2
capability with actual adapter code. The claim is KILLED regardless of the MCP argument.

---

## Residual Novelty Surface (if claim needs rescoping)

The only space that might survive audit:
- **Automatic conflict resolution** when two CLIs write contradictory facts to the same store
- **Zero-config discovery** — detecting all installed agentic CLIs and auto-wiring them to a
  shared memory layer without user intervention
- **Cryptographic provenance** — tracking which CLI wrote which memory fact for auditability

These are narrower claims and would need to be scoped precisely to survive.
