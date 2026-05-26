# N2 Cross-CLI Memory Bridging — Opus Final Verdict
**Date:** 2026-05-25T22:00:00Z
**Consolidator:** Opus
**Lanes consolidated:** A (academic), B (industry/OSS), C (adjacent fields)

---

## 1. Final verdict

**`dead-on-arrival`**

The claim "memory written from one agentic CLI retrieved and injected into another, with schema-bridging across CLI-specific storage formats" is *already shipped* in multiple production OSS systems and is operationally subsumed by AGENTS.md (a Linux Foundation standard) and Mem0's official Claude Code + Codex integrations. Lane A's "academically novel" verdict is correct only in the narrow sense that no *peer-reviewed paper* names Codex JSONL ↔ Cursor SQLite adapters — but novelty for a systems-engineering capability cannot be granted on the absence of a paper when half a dozen shipping repos and a vendor-blessed standard already deliver it. NeurIPS, ICSE, FSE, and ICLR reviewers would reject "we built X" claims when X is documented in vendor blogs, shipped in `mem0`, packaged in `memorix`, demoed on HN, and standardized in `AGENTS.md`. The B-lane kill is dispositive.

## 2. Confidence

**`high`**

Three independent search lanes converge: B found ≥10 OSS implementations naming the exact CLI pair (Claude Code + Codex) plus Mem0's *first-party documented integration* for both; C found a 40-year systems lineage (blackboard, KQML/FIPA, federated DB, LSP) plus the contemporary AGENTS.md standard; A found a closest-miss arxiv preprint (2605.11032) whose stated "future framework adapters" close even the narrow academic gap once the next iteration drops. Disagreement between lanes is jurisdictional (A measured papers; B measured products), not factual.

## 3. Top 3 closest prior works

1. **Mem0 — official Claude Code + Codex CLI integrations** (docs.mem0.ai/integrations/claude-code; mem0.ai/blog/how-memory-works-in-codex-cli; Composio toolkits for both). *Similarity:* "the same memory store that Codex writes to is the one that Cursor and Claude Code read from" — *literally* the N2 claim, scoped to `user_id` with schema normalization done inside Mem0's facts layer. *What it does NOT do:* expose the per-CLI adapter logic as a first-class research artifact, and does not solve write-conflict reconciliation across embedding models.
2. **Memorix (AVIDS2/memorix) + memory-bridge (Bbasche) + memsearch (zilliztech) + codex-agent-mem + agentmemory + mcp-memory-service + Hindsight + Pieces MCP** — explicit "cross-agent memory layer via MCP" for {Cursor, Claude Code, Codex, Windsurf, Gemini CLI, Copilot, Kiro, OpenCode, Antigravity, Trae} with shipped adapter code, knowledge graph, workspace sync, auto-memory hooks. *Similarity:* identical capability with public source. *What they do NOT do:* most lack systematic evaluation, calibrated retention policy, or longitudinal n=1 outcome measurement (N1's territory, not N2's).
3. **AGENTS.md (Linux Foundation; OpenAI/Anthropic/Google/AWS backing) + Hayes-Roth blackboard (1985) + KQML/FIPA-ACL (1990–1996) + LSP (2016)** — the standardization layer + the 40-year methodological lineage. *Similarity:* shared mutable substrate read by heterogeneous independently-authored agent processes is the textbook blackboard pattern; cross-vendor schema translation is exactly the FIPA ontology problem; LSP is the operational template (one server, many heterogeneous IDE clients, JSON-RPC sync). *What they do NOT do:* AGENTS.md is file-only and unidirectional read; classical work predates the *coding-CLI domain* and does not enumerate the specific schemas (Codex rollout JSONL etc.).

## 4. The exact surviving gap

Essentially nothing at the *capability* level. The narrowest unaddressed slice — and it is genuinely narrow — is:

**Runtime bidirectional write-merge across CLIs that use *different embedding/retrieval models*, with empirically-calibrated conflict resolution.** Mem0 normalizes at the facts layer but does not solve embedding-space disagreement; Memorix uses one knowledge graph; memory-bridge is journal-file sync (file-level, not semantic merge). No system in any lane shows a published *conflict-resolution policy* for the case where Claude Code's embedding says "memory X applies" and Codex's embedding says "memory X does not apply" on the same retrieval query. This is an OT/CRDT-adjacent open problem and is *plausibly* greenfield, but it is a different paper than N2 as written.

## 5. Repositioning recommendation

Drop the bridging claim entirely. Reposition as one of:

- **"Empirical study of cross-CLI memory transfer fidelity"** — measure information loss when memory written by Claude Code is retrieved by Codex through {Mem0, Memorix, AGENTS.md}. The contribution is the *measurement protocol and findings*, not the bridge.
- **"Conflict-resolution policies for cross-embedding agent memory"** — narrow systems contribution on the one residual gap.
- **Roll N2 into N1** as the substrate ("we ran a longitudinal n=1 deployment *using* the Mem0/Memorix bridge") and let N1 carry the novelty weight.

Do not submit N2 as a standalone novelty claim. It will be desk-rejected with citations to mem0 docs and AGENTS.md.

## 6. Falsification-test residual risk

**Low.** The B-lane researcher executed the falsification test the SPEC requires ("find any paper, repo, blog, or product that bridges memory between two distinct agentic CLIs") and returned ≥10 hits with URLs; the falsification standard is unambiguously met. Residual risk vectors:
- (a) Possibility that one of B's cited repos is misnamed/abandoned — irrelevant because Mem0 and AGENTS.md alone are dispositive vendor-backed standards.
- (b) Possibility that "Portable Agent Memory" (arxiv 2605.11032) was published *after* N2 was conceived — irrelevant under the SPEC's "any paper/repo/blog/product" standard, which is publication-date-blind.
- (c) Possibility that lane B over-counted by including general-purpose MCP memory servers (e.g., mcp-memory-service) that *can* be cross-CLI but were not pitched that way — mitigated because at minimum Mem0, Memorix, memory-bridge, memsearch, codex-agent-mem, and Hindsight are *explicitly pitched* as cross-CLI.

## 7. Per-researcher lane verdicts

| Lane | Verdict | Notes |
|---|---|---|
| **A (academic)** | SURVIVED (narrow) | Found "Portable Agent Memory" (2605.11032) as closest-miss; correctly notes it operates at model-API level not CLI level. Devil's advocate already concedes grey literature may kill the claim in IP/originality terms. |
| **B (industry/OSS)** | KILLED | Decisive. ≥10 named OSS/vendor implementations + HN posts + Mem0 official integration pages. Cites the exact CLI pair (Claude Code + Codex) repeatedly. |
| **C (adjacent fields)** | PARTIAL-OVERLAP → KILLED | Methodology is classical blackboard + FIPA + federated DB + LSP. Application domain (AI coding CLIs) is new; methodology is not. AGENTS.md cited as contemporary direct prior art. |

**Disagreement resolution:** A's "academically novel" verdict is a category error under the SPEC's falsification standard, which explicitly accepts "paper, repo, blog, or product." B's KILLED verdict therefore controls, and C's classical-lineage analysis converts the verdict from "merely product-shipped" to "product-shipped *and* methodologically pedestrian." Final: **`dead-on-arrival`**.

## 8. Reviewer-grade summary (≤150 words)

> The cross-CLI memory bridging claim does not survive even a cursory falsification pass. Mem0 ships first-party Claude Code and Codex integrations whose marketing copy is the claim verbatim; Memorix, memory-bridge, memsearch, codex-agent-mem, Hindsight, and Pieces are public OSS implementations covering the same CLI pairs with adapter code; AGENTS.md is now a Linux Foundation standard read natively by Codex/Copilot/Cursor/Windsurf/Amp. Methodologically the claim is blackboard architecture (Hayes-Roth 1985) plus FIPA-ACL ontology translation plus LSP-style heterogeneous-client state synchronization — a 40-year lineage. The academic-only "no peer-reviewed paper names these schemas" survival argument is a category error: the SPEC accepts any paper, repo, blog, or product, and the bar is met five times over. Recommend the authors either fold this into a longitudinal deployment study or pivot to the genuinely open sub-problem of conflict resolution across heterogeneous embedding spaces. As written: desk reject.
