# Sonnet B — Iteration 1: Broad OSS/Industry Sweep
Date: 2026-05-25T22:00:00Z
Auditor: Sonnet B (industry/OSS lane)
Claim: N3 — Per-project rule-lifecycle FSM with empirical decay calibration

## Systems Checked

### mem0 (mem0ai/mem0)
- Has "Memory Decay" feature (blog post confirmed).
- Implementation: search-time score multiplier, 0.3× (stale) to 1.5× (fresh), 5× spread.
- NOT an FSM — no named states, no state transitions.
- NOT empirically calibrated — fixed conservative band across workloads. Future roadmap item ("Per-project auto-tuning") explicitly deferred.
- Verdict: simple recency reweighting, not FSM + calibration.

### letta-ai/letta
- Memory model: Core Memory (Blocks), Recall Memory (messages), Archival Memory (passages).
- These are STORAGE TIERS, not lifecycle states.
- No evidence of FSM, state transitions, or decay.
- Block versioning exists for audit/undo, not lifecycle management.
- Verdict: no FSM, no decay.

### Anthropic MCP knowledge-graph-memory server
- Pure CRUD on entity/relation/observation graph.
- No lifecycle states, no TTL, no decay, no FSM.
- Verdict: not relevant.

### LangChain / LlamaIndex
- LangChain: session-scoped buffers; LangGraph uses sqlite checkpoints for state.
- No lifecycle FSM for memory items. No decay.
- LlamaIndex: session-scoped ChatMemoryBuffer, no expiration logic.
- Verdict: no FSM, no decay.

### Cursor / Continue.dev
- Cursor Memories (v1.0, mid-2025) removed in v2.1.x; replaced by static Rules files.
- No lifecycle FSM, no decay at any point.
- Verdict: irrelevant.

### SSGM framework (arxiv 2603.11768)
- References Weibull decay w(Δτ) = exp(−(Δτ/η)^κ) from prior work.
- Parameters η, κ are theoretical, NOT empirically calibrated.
- Describes read/write/reconciliation phases, not a named-state FSM.
- Explicitly framed as "conceptual governance architecture," no implementation.
- Verdict: closest theoretical analogue but not implemented, not calibrated.

### EverMemOS (arxiv 2601.02163)
- Three phases: Episodic Trace Formation → Semantic Consolidation → Reconstructive Recollection.
- Engram-inspired lifecycle mentioned in abstract.
- No evidence of explicit FSM with named states per memory item.
- No decay calibration.
- Verdict: pipeline stages, not per-item FSM.

### ByteRover (arxiv 2604.01599)
- Adaptive Knowledge Lifecycle (AKL): importance scoring + maturity tiers + recency decay.
- PDF not fully parseable; no evidence of explicit FSM or empirical calibration.
- Closest to a tiered lifecycle but unclear if states are formally named/transitioned.
- Verdict: possible partial overlap — needs closer read.

### Mastra-ai
- Multi-tier memory: history, working, semantic, observational.
- No FSM or decay mentioned in docs or DeepWiki.
- Verdict: no FSM, no decay.

### MCP ecosystem (doobidoo, alphaonedev, rohitg00)
- Some implement TTL tiers (6h / 7d / permanent) with usage-extended TTL.
- NOT an FSM — hardcoded time buckets, not a calibrated decay model.
- Verdict: simple TTL, not FSM + calibration.
