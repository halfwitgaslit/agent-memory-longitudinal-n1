# Loop 2 — COMPLETE

**Completed:** 2026-05-26T09:30:00Z
**Spend:** ~$2.50 of $200 cap (1.25% utilization)
**Tests:** 77/77 pass (baseline was 70 → +5 HONEST-Mem invariants +2 regression guards = 77)
**Git head:** 672121f (pushed to public repo halfwitgaslit/agent-memory-longitudinal-n1)
**Evidence dir:** `distillation/phd/decisions/loop2_evidence/`

## Per-deliverable status

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | Fix silent-failure reporting across backends | VALIDATED | `02_silent_failure_fixed.json` |
| 2 | Mem0 backend works end-to-end (via `claude -p`) | VALIDATED | `d2_mem0_e2e_report.json` |
| 3 | Injection skill fires in real Claude Code session | VALIDATED | `d3_skill_fires_report.json` |
| 4 | Arm switching null/random/mem0/letta | VALIDATED | `d4_arm_switching_report.json` |
| 5 | Cross-CLI bridging (Codex → Claude Code) | VALIDATED | `d5_cross_cli_bridging_report.json` |
| 6 | PDDC + GCMP on real-shaped data | VALIDATED | `d6_pddc_gcmp_report.json` |
| 7 | Hunt for other silent-failure modes | VALIDATED | `d7_silent_failure_hunt_report.json` |

## What's new in the codebase (vs. start of Loop 2)

### `memory/base.py`
- BackendHealth now includes: `last_error`, `last_error_ts_utc`, `n_silent_extraction_failures`
- `MemoryBackend.inspect()` RAISES on n_memories=-1 sentinel (HONEST-Mem invariant)
- New `MemoryBackend._record_error(kind, msg, silent_extraction=False)` helper

### `memory/claude_cli_llm.py` (NEW)
- Mem0-compatible LLM provider that routes calls through `claude -p` (subscription billing)
- Monkey-patches both `mem0.utils.factory.LlmFactory` and the LlmConfig validator
- Three-layer JSON discipline: hardened directive, one-shot retry, balanced-block extractor
- Module-level meter (calls, USD, tokens)

### `memory/mem0_backend.py`
- Auto-routes via `claude_cli` when ANTHROPIC_API_KEY is missing or placeholder
- `inspect()` refreshes n_memories from the live store on each call
- `_safe_count_memories()` uses Mem0 v2 `filters={"user_id":...}` API
- `search()` de-dups and trims to k (Mem0 hybrid search returns >k)
- Silent-failure detector now catches 4 mem0 error signals (was 2)

### `injection/claude_code_skill/`
- `retriever.py`: resolves the phd code dir via candidate list (env var → canonical default → in-tree)
- `retriever.py`: factory now accepts env overrides ROOMD_MEM0_STORE_DIR, ROOMD_MEM0_COLLECTION, ROOMD_LETTA_BASE_URL
- `SKILL.md`: invokes the phd code venv's Python (not system python3 which lacks pydantic)

### `tests/test_honest_mem_invariants.py` (NEW)
- 7 invariant tests covering the new BackendHealth contract

### `scripts/` (NEW)
- `d2_mem0_e2e.py` — end-to-end Mem0 + claude_cli + sentinel roundtrip
- `d3_skill_fires.py` — direct invocation + real claude -p verification
- `d4_arm_switching.py` — null/random/mem0/letta dispatch via env-var arm
- `d5_cross_cli_bridging.py` — Codex rollout ingest, Claude Code search
- `d6_pddc_gcmp.py` — PDDC fit + GCMP policy decisions
- `d7_silent_failure_hunt.py` — 6 edge cases vs HONEST-Mem invariants

## Architecture findings (documented, not fixed)

1. **Mem0 migrations qdrant shared lock**: Mem0 opens a global exclusive qdrant
   at `~/.mem0/migrations_qdrant`. Only ONE `Mem0Backend` instance can be alive
   per process. Documented in `mem0_backend.py` docstring. Phase 2 eval loop
   should keep one long-lived `Mem0Backend` per arm.

2. **Cross-CLI bridging requires scope discipline**: To bridge memories across
   Codex and Claude Code, OMIT `cli` from the scope hash OR use a fixed CLI
   marker on both writers and readers. The retriever today builds `cli` from
   `--scope-cli` (default "claude_code"). Phase 2 onboarding will need to
   document this.

3. **Codex sandbox/permissions boilerplate dilutes fact extraction**: First
   few Codex turns are env_context/sandbox_mode declarations, not real
   conversation. Phase 2 ingest should filter these before submission to mem0.

## Pre-registration

Pre-registration v1 (`preregistration/v1.md`, hash 14645d41...) is UNCHANGED.
`eval/experimental_constants.py` is UNCHANGED.
The pre-registration commit `4c913cd` remains the priority timestamp.

## Spend

Total claude_cli usage across Loop 2: ~$2.50
- D2: ~$0.10
- D3: ~$0.25 (real claude -p session)
- D4: ~$0.20 (mem0 seed)
- D5: ~$1.25 (Codex turn extraction + retries)
- D6: $0 (pure numpy + scipy, no LLM)
- D7: ~$0.70 (case 3 + case 4 LLM calls)

$197.50 of $200 cap remaining.

## Verification commands

To re-run any deliverable from scratch:

```bash
cd /Users/aiSandbox/github/claude_can_do_anything/distillation/phd/code
# Wipe persistent stores
rm -rf /tmp/phd_loop2_*qdrant ~/.mem0/migrations_qdrant
# Run each deliverable script
.venv/bin/python scripts/d2_mem0_e2e.py
.venv/bin/python scripts/d3_skill_fires.py
.venv/bin/python scripts/d4_arm_switching.py
.venv/bin/python scripts/d5_cross_cli_bridging.py
.venv/bin/python scripts/d6_pddc_gcmp.py
.venv/bin/python scripts/d7_silent_failure_hunt.py
# Full test suite
.venv/bin/python -m pytest tests/ -q
```

All scripts are idempotent — re-running after success will skip already-done work.

## Next action

Loop 2 closes the user-perspective-testing gap. The system is now demonstrably
functional end-to-end:
- A `claude -p` session in a roomd project will fire the skill, retrieve
  memories from any of the configured arms, and log every retrieval to
  `~/.roomd/mem_inject_log.jsonl`.
- Real Codex rollouts can be ingested under a bridge scope and surface in
  Claude Code searches.
- PDDC measurably improves out-of-sample over default FSRS-6.
- GCMP correctly classifies which memories propagate / promote per the
  pre-registered defaults.

**Ready for Phase 2 longitudinal deployment.** Vector can begin normal roomd
work; `ROOMD_MEM_ARM` per the pre-registered switchback schedule will
dispatch to the right backend; every retrieval is provenance-logged.
