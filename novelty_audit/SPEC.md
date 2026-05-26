# Novelty audit specification (Phase 0)

**Purpose:** falsify, not justify. The default assumption is "this has been done." Each candidate novelty claim N1-N4 is assigned a research team whose explicit job is to find prior work that kills the claim.

A claim survives only if 3 parallel researchers (running independently) all fail to find a paper, repo, blog, or product that does the same thing.

## Verdict scale (locked)

- `dead-on-arrival` — clear prior work exists that does exactly this
- `partial-overlap` — adjacent work exists; specific framing has a clear gap
- `novel-as-claimed` — no prior work found after exhaustive search across 3 independent researchers

## Per-team protocol

Each team has 3 Sonnet researchers running this loop, plus 1 Opus consolidator.

**Researcher A — Academic search.** arxiv, ACL Anthology, NeurIPS/ICLR/ICML/COLM/EMNLP proceedings, Google Scholar via WebFetch, Papers With Code. Focus: papers from Nov 2024 → May 2026, with secondary coverage of foundational older work that might already cover the claim. Output: top-10 closest papers ranked by similarity, with abstract + key methodological similarities/differences quoted.

**Researcher B — Industry & open-source search.** GitHub, HuggingFace, vendor blogs (Mem0/Letta/Hindsight/Cognee/Mastra/ByteRover/EverMemOS), Substack, Hacker News, Twitter/X via WebFetch, LessWrong, Notion-shared docs, conference workshops. Focus: production deployments, real-world write-ups, system READMEs, release notes. Output: top-10 closest products/repos/posts ranked by similarity.

**Researcher C — Adjacent-field search.** Information retrieval (TREC), recommender systems (RecSys), single-subject research design (psychology), n-of-1 trials (medical statistics), software engineering empirical studies (ICSE, FSE, MSR), continual learning, lifelong learning, episodic memory in cognitive science, BDI agents, case-based reasoning. The point is to find prior work that solves the same problem under different terminology. Output: top-10 closest works from outside ML/NLP, with the analogy made explicit.

**3-iteration loop per researcher** (per the protocol that worked for the 15-topic foundation research):
1. Research → write findings with cited examples
2. Devil's-advocate (what did I miss? what might be stale? what other angle should I try?)
3. Repeat 3×

**Opus consolidator** reads all 3 researchers' findings + devil's-advocate notes. Required output:
1. **Verdict** (`dead-on-arrival` / `partial-overlap` / `novel-as-claimed`)
2. **Top-3 closest prior works** across all 3 researchers, with quoted similarities
3. **The exact gap** (if `partial-overlap` or `novel-as-claimed`) — what would WE do that the closest works don't?
4. **Repositioning recommendation** if `dead-on-arrival` — is there an adjacent angle worth pursuing instead?
5. **Confidence level** (low / medium / high) based on search exhaustiveness

## Candidate novelty claims under audit

### N1. Longitudinal n=1 agent-memory deployment

Specifically: a single developer (or small team), deploying agent-memory systems (Mem0, Letta, Hindsight, etc. or hand-built) against their real coding work over weeks/months, with pre-registered protocol, randomized memory configurations across worktrees/sessions, and time-series outcome measurement (task success, time-to-solution, retry count, self-rated quality).

The single-subject longitudinal design is well-established in psychology and medicine (n-of-1 trials). The novelty claim is about applying this design specifically to agent-memory deployment, where the literature predominantly uses fixed-corpus benchmarks (LongMemEval, LoCoMo, MemoryArena, BEAM, etc.) rather than personal-deployment longitudinal studies.

**Falsification standard:** find any longitudinal n=1 deployment of an agent-memory system with > 50 real sessions, pre-registered, time-series outcomes. Or: any "in the wild" deployment study of Mem0/Letta/Hindsight with real-user outcomes (not just benchmark scores).

### N2. Cross-CLI memory bridging

Specifically: memory records written from sessions in one agentic CLI (e.g., Codex) retrieved and injected into sessions in a different agentic CLI (e.g., Claude Code) on the same underlying project. Requires schema-bridging between the source-format differences (Codex rollout JSONL vs Claude Code JSONL vs Cursor SQLite vs Cline JSON, etc.). The memory store is the shared substrate; the CLI-specific adapters translate.

**Falsification standard:** find any paper, repo, blog, or product that bridges memory between two distinct agentic CLIs (any pair). Mem0/Letta/Cognee SDKs can ingest from anywhere, so the relevant question is: has anyone published or productized an actual bridge with adapters for two specific CLIs.

### N3. Per-project rule-lifecycle FSM with empirical decay calibration

Specifically: a finite-state-machine for memory records (draft → active → deprecated → archived) with state transitions driven by empirical usage data (support_count, hit-rate, conflict-detection events, time since last use), and decay parameters CALIBRATED from real session data rather than chosen by hand.

Phase B/C research said this was greenfield. Re-verify with fresh searches.

**Falsification standard:** find any published rule/memory system with explicit lifecycle FSM AND empirically calibrated decay parameters. FadeMem (decay formula published) doesn't count unless it calibrates against deployment data. Library Drift (evidence-gated retirement) is the closest known candidate.

### N4. Worktree-aware memory

Specifically: agent memory that is aware of git worktree structure — each new worktree starts with the accumulated learnings of its parent branch's prior worktrees, while keeping its own learnings isolated until merged back. The 32-worktree-fleet pattern in Vector's roomd corpus is the use case.

**Falsification standard:** find any branch-aware or worktree-aware agent-memory system. LangGraph state per-thread doesn't count. Letta block-scoping by user doesn't count. The specific claim is git-worktree-awareness in the memory layer itself.

## Output locations

Per team, in `phd/novelty_audit/<Nid>_<slug>/iterations/2026-05-25T22-00-00Z/`:
- `sonnet_a_findings.md`, `sonnet_a_devils.md`, `sonnet_a_sources.json`
- `sonnet_b_*.md/.json` (same)
- `sonnet_c_*.md/.json` (same)
- `opus_verdict.md` (the consolidated verdict)

`current/verdict.md` symlinks/copies the latest opus output for downstream readers.
