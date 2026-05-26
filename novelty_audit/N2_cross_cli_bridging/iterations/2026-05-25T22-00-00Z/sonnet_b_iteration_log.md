# Sonnet B — Industry/OSS Research Log
# N2: Cross-CLI Memory Bridging
# Date: 2026-05-25T22:00:00Z
# Researcher: B (industry/OSS subset)

## Iteration 1 — GitHub repos, Mem0, Letta

### Queries
- "cross-CLI memory bridge Claude Code Codex shared memory agent tools 2025 2026"
- "Mem0 claude code codex cursor integration memory bridge"
- "Letta MCP server cross-CLI memory agentic tools"

### Findings

**Memorix (AVIDS2/memorix)** — GitHub + mcpservers.org listing. Explicitly advertises:
"Open-source cross-agent memory layer for coding agents via MCP. Compatible with Cursor,
Claude Code, Codex, Windsurf, Gemini CLI, GitHub Copilot, Kiro, OpenCode, Antigravity, and Trae."
Has adapter code, MCP server, knowledge graph, workspace sync, auto-memory hooks.
URL: https://github.com/AVIDS2/memorix

**memory-bridge (Bbasche/memory-bridge)** — GitHub. "Two-way memory sync between AI coding
agents (Claude Code, Codex, and more)." Codex writes to project/memory/ dated journal files;
memory-bridge syncs to Claude Code prefixed by project name.
URL: https://github.com/bbasche/memory-bridge

**agentmemory** — blog post + tool. "Shared memory layer for AI coding tools across Claude Code,
Codex CLI, Cursor, Gemini CLI, OpenCode, and other MCP-compatible tools."
URL: https://knightli.com/en/2026/05/19/agentmemory-persistent-memory-ai-coding-agents/

**memsearch (zilliztech/memsearch)** — "persistent, unified memory layer for all your AI agents
(e.g. Claude Code, Codex), backed by Markdown and Milvus. Memories written from any agent
searchable from every other agent."
URL: https://github.com/zilliztech/memsearch

**Mem0** — official docs confirm: memory scoped to user_id (not tool). "The same memory store that
Codex writes to is the one that Cursor and Claude Code read from." Has Claude Code integration
page and Codex CLI integration page. Composio documents both integrations.
URLs:
- https://docs.mem0.ai/integrations/claude-code
- https://mem0.ai/blog/how-memory-works-in-codex-cli
- https://composio.dev/toolkits/mem0/framework/codex
- https://composio.dev/toolkits/mem0/framework/claude-code

**Letta** — has MCP server (oculairmedia/Letta-MCP-server) and Letta Code (memory-first coding
agent). Primarily per-agent persistent memory; cross-CLI bridging is indirect (any tool pointing
at Letta API gets same memory store).
URL: https://github.com/letta-ai/letta-code

**claude_codex_bridge (bfly123/claude_code_bridge)** — "Visible multi-agent CLI teams for
Claude, Codex, Gemini, OpenCode, and Droid with project memory and tmux supervision."
URL: https://github.com/bfly123/claude_code_bridge

---

## Iteration 2 — MCP ecosystem, Hacker News, Cognee/Mastra/ByteRover

### Queries
- "MCP memory server works across multiple agentic CLIs Cursor Cline Continue Aider 2025 2026"
- Hacker News "bridged Claude Code and Codex memory" shared memory across AI coding tools
- "Cognee Mastra ByteRover cross-CLI memory integration coding agents"

### Findings

**Pieces MCP Server** — "Works with Cursor and GitHub Copilot (and soon Cline and many more)."
Long-term memory across whichever tools are connected.
URL: https://pieces.app/blog/introducing-the-pieces-mcp-server

**ai-memory MCP** — "works with Claude, ChatGPT, Grok, Cursor, Windsurf, and any MCP client."
URL: https://mcpservers.org/servers/alphaonedev/ai-memory-mcp

**Memory Bank MCP** — "works with Cline, Claude, Cursor, and any other MCP client."
URL: https://github.com/alioshr/memory-bank-mcp

**Hacker News — Show HN: OpenTimelineEngine** — "Shared local memory for Claude Code and codex"
URL: https://news.ycombinator.com/item?id=47187858

**Hacker News — Show HN: Mimir** — "Shared memory and inter-agent messaging for Claude Code swarms"
URL: https://news.ycombinator.com/item?id=47064865

**Hindsight (vectorize.io)** — published guide: "Both Claude Code and OpenClaw can point at the
same Hindsight bank, enabling them to read and write the same bank."
URL: https://hindsight.vectorize.io/guides/2026/04/20/guide-openclaw-and-claude-code-shared-memory

**claude-mem GitHub discussion #1329** — Feature request to make claude-mem usable as shared
memory backend for Codex-style agents (not only Claude Code). Shows demand + partial existing art.
URL: https://github.com/thedotmack/claude-mem/discussions/1329

**ByteRover CLI** — "gives AI coding agents persistent, structured memory... sync to cloud,
share across tools and teammates."
URL: https://github.com/campfirein/byterover-cli

**Cognee** — MCP published, cross-framework memory control plane. Not specifically cross-CLI for
coding agents; more general agent framework memory. Has cognee-mcp that any MCP client can use.
URL: https://www.cognee.ai/blog/cognee-news/introducing-cognee-mcp

**Mastra** — Memory Processors for agent pipelines; no specific cross-CLI coding agent feature.

---

## Iteration 3 — MCP-as-bridge argument, Obsidian/Rewind ecosystem

### Queries
- MCP protocol "cross-CLI memory" memory server shared across Claude Code Codex argument bridge
- "Rewind Reor Logseq Obsidian Claude Code Codex memory tap multiple agentic CLI"

### Findings

**codex-agent-mem** — "portable MCP memory layer designed for MCP-compatible runtimes including
Codex CLI/Desktop, Claude Code, Google Gemini CLI, Qwen Code workflows."
URL: https://marcelocaporale.github.io/codex-agent-mem/

**codebase-memory-mcp (DeusData)** — cross-agent memory with knowledge graph, any MCP client.
URL: https://github.com/DeusData/codebase-memory-mcp

**mcp-memory-service (doobidoo)** — "Multiple agents can use mcp-memory-service as shared state
and inter-agent messaging bus." Supports Claude Code, Gemini CLI, Codex CLI, other HTTP clients.
URL: https://github.com/doobidoo/mcp-memory-service

**obsidian-second-brain** — "Cross-CLI skill for Obsidian. Turns your vault into a living
AI-first second brain across Claude Code, Codex CLI, Gemini CLI, and OpenCode."
URL: https://github.com/eugeniughelbur/obsidian-second-brain

**obsidian-mind (breferrari)** — "Obsidian vault that gives AI coding agents persistent memory.
Claude Code, Codex CLI, Gemini CLI."
URL: https://github.com/breferrari/obsidian-mind

**obsidian-wiki (Ar9av)** — "multi-agent ingest from Claude Code history, Codex sessions,
Hermes memories, OpenClaw, Pi sessions, Windsurf data."
URL: https://github.com/ar9av/obsidian-wiki

**MindStudio blog** — "How to Build a Self-Evolving Claude Code Memory System With Obsidian
and Claude Code Hooks"
URL: https://www.mindstudio.ai/blog/self-evolving-claude-code-memory-obsidian-hooks

**Codex issue #12558** — feature request to implement Claude Code-style /rewind inside Codex.
Confirms cross-contamination of patterns but not shared memory.

**codex-agent-mem** explicitly states: "portable MCP memory layer" across
"Codex CLI/Desktop, Claude Code, Google Gemini CLI, Qwen Code workflows."

**Codex as MCP server** — OpenAI Codex can itself run as MCP server so other MCP clients
(Claude Desktop, etc.) can call Codex as a tool. This creates bidirectional interop at protocol
level beyond just memory.
