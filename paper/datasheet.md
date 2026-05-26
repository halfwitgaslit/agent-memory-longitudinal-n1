# Datasheet for the RoomD Coding-CLI Corpus (v1, 2026-05-25)

Following Gebru et al. (2021), "Datasheets for Datasets," CACM 64(12).

**Corpus identifier:** `roomd-cli-corpus-v1`
**Release status:** Phase 1 internal; planned public release CC-BY-NC on paper acceptance
**Release URL (planned):** TBA (Zenodo or HuggingFace Datasets)
**Croissant metadata:** TBA on release
**EvalCards entry:** TBA on release (per E3 dataset-ethics consolidated)

---

## 1. Motivation

### 1.1 For what purpose was the dataset created?

The corpus was assembled to support the longitudinal n=1 deployment evaluation of
agent-memory frameworks on a real developer's coding work. Existing agent-memory
benchmarks (LongMemEval, LoCoMo, MemoryArena, BEAM, MemoryCode, PersonaMem-v2,
SWE-Bench-CL) use fixed corpora rather than personal-deployment longitudinal data,
making them unable to measure utility on a developer's *evolving* real work.

### 1.2 Who created the dataset?

Vector (pseudonym), the single subject of this n=1 study. Self-collected from
their own developer workstation during 2026-04 through 2026-05.

### 1.3 Who funded the creation?

Self-funded. Subscription costs (Anthropic Pro, OpenAI Plus) are part of
Vector's normal developer tooling. No external compute or labor was used.

### 1.4 Any other comments?

The corpus is by-design a *snapshot* of one developer's workflow over ~6 weeks.
Generalizability claims are explicitly bounded to n=1 inference; the paper makes
no population-level claims.

---

## 2. Composition

### 2.1 What do the instances represent?

Two kinds of instances:

- **Claude Code sessions:** 176 JSONL session logs from a roomd-tagged Anthropic
  Claude Code workspace, across 42 project directories (main + 32 git worktrees
  + 9 misc roomd-adjacent projects: roomd-RCAEval-benchmarking + sandboxes,
  roomd-agent-orchestration, roomd-memory).
- **Codex sessions:** 610 JSONL rollout logs from OpenAI Codex CLI sessions
  whose `session_meta.cwd` contains "roomd", filtered from a superset of 924
  total Codex sessions on the workstation.

Total: 786 sessions, ~62M billable tokens, ~13.4B cache-read tokens (from the
project Phase 0 inventory).

### 2.2 How many instances are there in total?

786 sessions in Phase 1 release. The Phase 2 deployment extends this with
~120 newly-collected sessions under randomized arm assignment.

### 2.3 Does the dataset contain all possible instances?

No. The Phase 1 release covers all roomd-related Claude Code and Codex sessions
on Vector's workstation as of 2026-05-25. Sessions from non-roomd projects
(e.g., this distillation project) are excluded. Cursor, Windsurf, Cline, and
other CLIs are excluded by scope (per the locked architecture).

### 2.4 What data does each instance consist of?

Each Claude Code JSONL session contains:
- `user` records: user prompts with `message.role`, `message.content` (string
  for early-format or list of content blocks for current format)
- `assistant` records: model responses with `usage`, `model`, content blocks
  including text, thinking, tool_use, tool_result
- `system` records: stop_hook_summary and other lifecycle events
- `attachment`, `queue-operation`, `last-prompt`, `ai-title`, `pr-link` records

Each Codex JSONL rollout contains:
- `session_meta`: id, cwd, originator, cli_version, base_instructions
- `turn_context`: per-turn metadata
- `response_item`: messages, function_calls, function_call_outputs, reasoning
- `event_msg`: lifecycle events (task_started, exec_command_end, token_count, ...)

All instances are timestamped (ISO 8601 UTC) and include a stable session_id
(UUID for Claude Code, UUIDv7 for Codex).

### 2.5 Is there a label or target?

No labels in Phase 1. The Phase 2 deployment adds per-task labels
(`task_success_binary`, `task_success_5pt`, `prior_knowledge_recall`,
`had_to_remind_count`) from the subject's post-task self-reports and from a
multi-judge LLM-grading pass with κ ≥ 0.7.

### 2.6 Is any information missing from individual instances?

- Some Claude Code records have empty `message.content` (e.g., abandoned turns).
- Codex `reasoning.encrypted_content` is opaque (encrypted CoT).
- Tool outputs longer than 25,000 tokens are truncated in Claude Code by the
  built-in Read tool; we record the truncation marker but not the original.
- Cache pricing in `total_token_spend_usd` is approximated (see metrics.py
  for the per-model rate table).

### 2.7 Are relationships between individual instances made explicit?

Yes. Claude Code records contain `parentUuid` chains; Codex `response_item.payload.call_id`
correlates function_call ↔ function_call_output. The adapter (`adapters/`)
reconstructs these into `Turn.parent_turn_id` and `ToolEvent.parent_turn_id`.

Cross-session links (e.g., one session forked from another) are encoded:
- Codex: `session_meta.forked_from_id`
- Claude Code: no native fork; we use temporal + cwd proximity as a heuristic
  (not in Phase 1 release).

### 2.8 Are there recommended data splits?

Yes (per locked architecture/v1.md §5):
- **PDDC calibration:** 70% in-deployment trajectories for fitting, 30%
  held-out for parameter-set selection
- **Decontamination:** no held-out test set is used for tuning model parameters
- **Multi-judge κ:** 10% manual spot-check stratified by arm

### 2.9 Are there any errors, sources of noise, or redundancies?

Yes:
- ~20% of session JSONLs are < 50 KB (very short sessions, often early aborts);
  Phase 1 metrics filter these by min_size in adapter tests
- Some sessions are restarts/forks of the same logical task (Codex `forked_from_id`);
  this is preserved as metadata, not collapsed
- The reminder-count regex (`metrics.py`) misses paraphrases; we report
  agreement on 10% manual spot-check

### 2.10 Is the dataset self-contained, or does it rely on external resources?

The corpus is self-contained as raw JSONL. The adapter requires Python 3.13 +
Pydantic 2; reproduction requires the frozen requirements
(`requirements_frozen.txt`).

### 2.11 Does the dataset contain confidential, offensive, or personal data?

- **Personal data:** the corpus contains user prompts authored by the subject.
  All prompts are technical (roomd is an open-source MCP framework). No PII
  about third parties is present.
- **Anonymization:** the subject is identified only as "vector" in the release.
  Real-world identity is documented in the consent record but not in the
  corpus.
- **Confidential code:** roomd is open-source (Apache 2.0). The corpus may
  contain in-flight code snippets that pre-date the public release; we audit
  for any non-public code before release.
- **Offensive content:** none identified; the subject's communication style is
  professional. A pre-release audit pass will scan with a slur/profanity
  filter.

---

## 3. Collection process

### 3.1 How was the data acquired?

Automatic logging by Claude Code (writes JSONL to `~/.claude/projects/`) and
Codex CLI (writes JSONL to `~/.codex/sessions/`). The subject took no
explicit action to log; this is the standard behavior of both CLIs.

### 3.2 What mechanisms were used?

- Anthropic Claude Code CLI v2.1.x (2026-04-2026-05)
- OpenAI Codex CLI v0.118 - v0.122 (2026-04-2026-05)
- Both billed against subscription tiers (Anthropic Pro, OpenAI Plus)

### 3.3 Sampling

Convenience sample. The subject does not pre-select sessions to include; ALL
roomd-related sessions in the date range are included. The Phase 2 deployment
will add intentional arm-randomized sessions.

### 3.4 Who was involved in collection?

The subject only. No paid annotators or external participants.

### 3.5 Over what timeframe?

2026-04 to 2026-05 (~6 weeks) for the Phase 1 baseline. Phase 2 adds the
4-6 week longitudinal arm-randomized data.

### 3.6 IRB / ethical review?

n=1 self-collected dataset with self-given consent. The subject's IRB
equivalent: they reviewed the consent form, signed it, and stored it with the
corpus metadata. No third-party IRB was engaged.

---

## 4. Preprocessing / cleaning / labeling

### 4.1 Was any preprocessing done?

Only the adapter parsing (`adapters/`); the raw JSONL is preserved on disk
and re-parseable.

### 4.2 Was the "raw" data saved?

Yes. The raw JSONL files are preserved at their original locations
(`~/.claude/projects/`, `~/.codex/sessions/`). The adapter is read-only.

### 4.3 Is the software available?

Yes, MIT-licensed at `phd/code/` (see release).

---

## 5. Uses

### 5.1 Has the dataset been used for any tasks?

Yes. Phase 1: substrate for the longitudinal n=1 evaluation of agent-memory
frameworks. The Phase 0 audit also used the corpus inventory for substrate
verification.

### 5.2 Is there a repository linking to other papers/systems using the dataset?

Phase 1 has one entry: this paper. Future entries will be added to a
public README on the release URL.

### 5.3 What other tasks could the dataset be used for?

- Evaluation of other agent-memory systems (the adapter is open-source)
- Studies of developer-AI interaction patterns
- Coding agent fine-tuning data (subject to license)
- Tool-use pattern analysis (the tool_events are explicit)

### 5.4 What should users know to avoid harms?

- The corpus is n=1. Do not generalize to populations without additional data.
- Time-of-day effects are documented (per E2 ~20% variance); analyses ignoring
  time strata risk confounds.
- The subject is highly technical; results may not transfer to novice users.

### 5.5 Tasks the dataset should NOT be used for?

- Training a model that impersonates Vector
- Training a model that produces non-consensual content
- Inferring Vector's real-world identity from the corpus
- Population-level developer-productivity claims

---

## 6. Distribution

### 6.1 Will the dataset be distributed?

Yes. Planned release on paper acceptance.

### 6.2 How will it be distributed?

- Public archival: Zenodo with DOI
- Mirror: HuggingFace Datasets (if size allows)
- Self-hosted: the project repo

### 6.3 When will it be distributed?

On acceptance at the target venue (ICLR 2027 main track, target deadline
Sep-Oct 2026). arXiv pre-print of the paper accompanies submission.

### 6.4 License?

**CC-BY-NC 4.0** for the corpus (per E3 dataset-ethics consolidated). The
NonCommercial clause protects against commercial training without
attribution + permission.

The system code is **MIT-licensed**.

### 6.5 Restrictions / export controls?

None. The corpus contains no restricted content. ECCN: not applicable.

---

## 7. Maintenance

### 7.1 Who is hosting?

The subject, with mirroring on Zenodo (planned).

### 7.2 How to contact?

(Email TBA on release; for the Phase 1 internal version, contact via the
project repo issues.)

### 7.3 Will the dataset be updated?

Versioned releases. Phase 2 adds longitudinal arm-randomized data. Subsequent
phases (if pursued) add cross-subject replication.

### 7.4 Will obsolete versions be kept?

Yes. Zenodo provides versioning; old DOIs remain accessible.

### 7.5 Mechanism for others to extend/augment?

Pull requests welcome on the system repo; corpus contributions require an
adjusted IRB process.

---

## Appendix A: Provenance summary

| Field | Value |
|---|---|
| Source paths (Claude Code) | `~/.claude/projects/-Users-aiSandbox-github-roomd*` (42 dirs, 176 JSONL ≥ 0 bytes; tests use ≥ 50 KB filter) |
| Source paths (Codex) | `~/.codex/sessions/**/*.jsonl` + `~/.codex/archived_sessions/*.jsonl` (924 total; 610 with cwd~"roomd") |
| Adapter | `phd/code/adapters/{claude_code_jsonl,codex_rollout_jsonl}.py` (lossless round-trip; 34 pytest tests) |
| Unified schema | `phd/code/adapters/schema.py` (Pydantic v2, version v1.0) |
| Collection window | 2026-04-01 to 2026-05-25 |
| Subject | "vector" (pseudonym; identity sealed in consent record) |
| Anonymization audit | TBA on release |
| Decontamination certification | No external benchmark sets present; PDDC train/test split documented in `eval/experimental_constants.py` |
