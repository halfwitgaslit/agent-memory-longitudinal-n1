# Sonnet C — Adjacent Fields Audit: N2 Cross-CLI Memory Bridging
**Date:** 2026-05-25T22:00:00Z  
**Auditor lane:** Outside-ML/NLP classical systems literature  
**Task:** FALSIFY

---

## Evidence by Domain

### 1. Blackboard Architecture (STRONGEST HIT)
Hayes-Roth (1985) and Engelmore & Morgan (1988) define the blackboard as a **shared persistent workspace where heterogeneous, independently-authored knowledge sources read and write**. This is structurally identical to N2: a central store that agents (here: CLI tools from different vendors) access without knowing each other's internals. The pattern: heterogeneous reasoners → shared mutable store → no peer-to-peer coupling. Recent LLM work (arXiv 2510.01285, 2507.01701) explicitly revives this pattern for multi-agent LLM systems, confirming its direct relevance.

### 2. KQML / FIPA-ACL (STRONG HIT)
DARPA's KQML (1990) and FIPA-ACL (1996) standardize **cross-vendor agent knowledge sharing via shared virtual knowledge bases**. Agents from different vendors expose and query a common semantic layer. This covers N2's "bridging" concern at the protocol level. The schema-translation problem N2 claims to solve (mapping one CLI's memory format to another's) is exactly what FIPA ontology support handles.

### 3. Federated Databases (STRONG HIT)
Sheth & Larson (1990, ACM Computing Surveys) and Özsu & Valduriez (1991) establish **federated schema integration** as a solved sub-problem: autonomous heterogeneous data stores expose a unified query interface without surrendering autonomy. This covers the structural problem of N2 (different tools have different memory schemas; bridge provides unified read/write).

### 4. LSP / IDE Plugin Architecture (MODERATE HIT)
The Language Server Protocol (Microsoft, 2016) shows how **a single server process maintains shared in-memory state that multiple heterogeneous IDE clients** (VS Code, Vim, Emacs, JetBrains) consume via a standard JSON-RPC protocol. The document-sync model (didOpen/didChange/didClose) is a real-time shared memory protocol across heterogeneous clients. This is operationally close to N2's runtime memory bridge.

### 5. Federated SPARQL / Semantic Web (MODERATE HIT)
W3C SPARQL 1.1 Federated Query (2013) routes sub-queries across heterogeneous RDF endpoints and returns unified results. The schema bridging is done at the ontology/RDF layer. Directly analogous to N2's cross-CLI context normalization.

### 6. PIM / Memex (WEAK — CONCEPTUAL ONLY)
Bush (1945) through modern PKM tools establishes cross-tool aggregation as a user-level goal, but does not operationalize it as a machine-to-machine protocol. Low direct overlap.

### 7. AGENTS.md Ecosystem (DIRECT PRIOR ART — CONTEMPORARY)
By late 2025, AGENTS.md (Linux Foundation, backed by OpenAI/Anthropic/Google/AWS) is a file-based shared memory layer that multiple CLI coding agents (Codex, Copilot, Cursor, Windsurf, Amp) read natively. Amp reads both AGENTS.md and CLAUDE.md — a practical cross-CLI bridge already deployed in production. This is not classical literature but is directly on-claim and predates any novel N2 publication.

---

## Verdict-in-My-Lane: PARTIAL-OVERLAP (tending toward KILLED)

**Methodology is not novel.** The N2 claim describes:
1. Shared mutable memory readable by heterogeneous agents → **Blackboard (1985)**
2. Cross-vendor agent communication with schema translation → **KQML/FIPA-ACL (1990–1996)**
3. Federated heterogeneous data with unified interface → **Federated DB (1990–1991)**
4. Single state server consumed by multiple heterogeneous tool clients → **LSP (2016)**

The *application domain* (AI coding CLIs) is new, but the methodology has clear classical-AI and systems antecedents at every layer. The closest live instantiation (AGENTS.md ecosystem) already delivers a subset of N2 in production without novel architectural contribution.

**What might survive:** A narrow claim about *runtime* (not file-based) bidirectional memory sync with conflict resolution across CLIs with different embedding/retrieval models — if that specific combination is unaddressed. The "bidirectional write + merge" problem has overlap with operational transformation (OT/CRDTs in collaborative editing, e.g., Google Docs, 2006+) which should also be checked by Researcher A/B.

**Recommendation:** Downgrade N2 from "novel methodology" to "novel application." Require explicit differentiation from blackboard architecture and LSP in any paper draft.

---

## Sources
- Hayes-Roth (1985), "A blackboard architecture for control," *Artificial Intelligence* 26(3)
- Engelmore & Morgan (1988), *Blackboard Systems*, Addison-Wesley
- arXiv:2510.01285 — LLM-Based Multi-Agent Blackboard System (2025)
- arXiv:2507.01701 — Advanced LLM Multi-Agent Systems Based on Blackboard Architecture (2025)
- Sheth & Larson (1990), "Federated Database Systems," *ACM Computing Surveys* — https://dl.acm.org/doi/10.1145/96602.96604
- FIPA-ACL / KQML comparison — https://www.academia.edu/88620133/Agent_Communication_Languages_Comparison_Fipa_Acl_and_KQML
- LSP official spec — https://microsoft.github.io/language-server-protocol/
- W3C SPARQL 1.1 Federated Query — https://www.w3.org/TR/sparql11-federated-query/
- AGENTS.md cross-tool adoption — https://vibecoding.app/blog/agents-md-guide
