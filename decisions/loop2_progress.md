# Loop 2 Progress Log

Append-only log of meaningful state changes during Loop 2 (end-to-end empirical validation).

## 2026-05-25T00:00:00Z — START

- Baseline established: 70/70 tests pass on commit `4c913cd`.
- Critical bug confirmed from user-perspective E2E smoke: Mem0 backend reports `n_errors=0`, `n_memories=-1` when ANTHROPIC_API_KEY is placeholder. Backend declares itself "healthy" while storing nothing.
- Spend so far this loop: $0.00
- Working directory: `/Users/aiSandbox/github/claude_can_do_anything/distillation/phd/code`
- Evidence dir: `distillation/phd/decisions/loop2_evidence/`

## Plan

7 deliverables required, each empirically validated with shell evidence captured to disk:

1. Fix silent-failure reporting (no `-1` sentinel; surface zero-extraction as error; add `last_error`)
2. Get Mem0 or Letta to actually work end-to-end via `claude -p` LLM shim
3. Verify injection skill fires in a real Claude Code session
4. Test arm switching end-to-end (null, random, mem0, letta)
5. Test cross-CLI bridging (Codex → Claude Code)
6. Test PDDC + GCMP on real-shaped data
7. Fix any other silent-failure modes discovered

Methodology: fix → re-run pytest → capture E2E evidence → commit → push.

## 2026-05-26T08:15:00Z — D3 VALIDATED

Fixed two real silent-failure modes surfaced by D3 Part B (claude -p with installed skill):

1. `ModuleNotFoundError: No module named 'memory'` — retriever's `sys.path.insert(parents[2])` resolved to `~/.claude` when installed there. Fixed via env-var + canonical-path candidate list.
2. `ModuleNotFoundError: No module named 'pydantic'` — system `python3` lacks venv deps. Fixed by updating SKILL.md to invoke `$ROOMD_PHD_VENV_PYTHON` (default: phd code's `.venv/bin/python`).

Both fixes mirrored to installed copy at `~/.claude/skills/roomd-memory-retrieval/`.

Re-ran D3 with fixes:
- Part A: both arms (null, random) directly invoked → `status: "OK"`, log lines appended.
- Part B: real `claude -p` session in temp roomd fixture; cost $0.15; skill fired; log entry `{"arm": "null", "n_results": 0, "status": "OK", "latency_ms": 50}`; Claude reported "The retriever ran successfully but found no memories for the query".

Evidence: `decisions/loop2_evidence/d3_skill_fires_report.json`.
Tests: 75/75 still pass.
Cumulative loop2 spend: ~$1.05.

