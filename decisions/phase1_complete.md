# Phase 1 — Complete

**Date completed:** 2026-05-26T03:00:00Z
**Spend:** $0.00 of $500 cap (cumulative $29.07 carried from HMA-1)
**Test pass rate:** 70/70 (100%)
**Pre-registration hash:** `14645d41cc73fe32f82d8ac4ba9b6aa0940750be244d0473a3f29553b21b6fea`

## Deliverables map

| ID | Deliverable | Path(s) | Status | Verification |
|---|---|---|---|---|
| **A** | Architecture document | `phd/architecture/v1.md` (10 sections, 10 KB) | COMPLETE | Locked v1.0 |
| **B** | Adapters (Claude Code + Codex + unified schema + tests) | `phd/code/adapters/{schema,claude_code_jsonl,codex_rollout_jsonl}.py` + `phd/code/tests/test_adapters.py` | COMPLETE | 34/34 tests pass on 10+10 real roomd sessions |
| **C** | Memory backends (6 wrappers + ABC + smoke tests) | `phd/code/memory/{base,null,random,mem0,letta,hindsight,cognee}_backend.py` + `phd/code/tests/test_memory_smoke.py` | COMPLETE | 7/7 smoke tests pass. Smoke summary: `phd/code/fixtures/memory_smoke_summary.json` |
| **D** | Novel layer (PDDC + GCMP + HONEST-Mem reporter) | `phd/code/calibration/decay.py` + `phd/code/governance/cross_worktree.py` + `phd/code/reporting/honest_mem.py` + tests | COMPLETE | 8 PDDC + 8 GCMP tests pass; PDDC recovers truth on synthetic data |
| **E** | Injection mechanism (Claude Code skill + Codex hook) | `phd/code/injection/claude_code_skill/{SKILL.md,retriever.py}` + `phd/code/injection/codex_prompt_hook/inject.sh` | COMPLETE | End-to-end smoke (null + random arms); logs to `~/.roomd/mem_inject_log.jsonl` |
| **F** | Eval harness (runner + metrics + stats + pre-registration) | `phd/code/eval/{runner,metrics,stats,experimental_constants,pre_registration}.py` + tests | COMPLETE | 13/13 tests pass; ran on 30 real sessions, 0 errors |
| **G** | Pre-registration document | `phd/preregistration/v1.md` (154 lines, hash 14645d41…) | COMPLETE | Hash locked; awaiting git commit to lock priority timestamp |
| **H** | Datasheet | `phd/paper/datasheet.md` (12 KB, Gebru et al. 2021 format) | COMPLETE | Covers all 7 Gebru sections + provenance appendix |
| **I** | Paper draft v0.1 | `phd/paper/v0.1.md` (25 KB) + `phd/paper/v0.1.pdf` (113 KB) | COMPLETE | All 12 mandatory Phase 0 citations present in paragraph 1 / related work |
| **J** | Reproducibility package (Dockerfile + Makefile + frozen reqs) | `phd/code/{Dockerfile,Makefile,requirements_frozen.txt}` + `phd/code/paper_build.py` | COMPLETE | `make smoke` runs 70 tests; `make paper` renders the PDF |

## Verification gate (per build instructions § "Verification gate")

✅ `make smoke` succeeds for all 4 memory backends + 2 baselines (Letta documented SKIPPED-UNHEALTHY per architecture)
✅ All 3 adapter round-trip tests pass (Claude Code + Codex + cross-CLI normalization)
✅ Injection skill demonstrably runs end-to-end and emits a valid markdown block
✅ PDDC fits parameters on synthetic dataset with known ground truth (5/5 sign-match, 20× loss reduction)
✅ Pre-registration document exists with a SHA-256 hash
⏳ Hash NOT YET committed to git — the commit IS the priority timestamp (Phase 2 prerequisite)
✅ v0.1 paper draft compiles to PDF (113 KB)
✅ All claims in the paper are backed by citation (12 mandatory from Phase 0) or flagged as `conjecture` (Phase 2 results explicitly out-of-scope for v0.1)

## Where to start Phase 2

1. `cd distillation/phd && git init && git add preregistration/v1.md && git commit -m "PRE-REGISTRATION HASH 14645d41…"` — this locks the priority timestamp.
2. (Optional) push to a public repo or post to OSF for additional public timestamping.
3. Start a local Letta server in Docker: `docker run -d -p 8283:8283 letta/letta:latest`.
4. Install the Claude Code skill: `cp -r phd/code/injection/claude_code_skill ~/.claude/skills/roomd-memory-retrieval/`.
5. Set `ROOMD_MEM_ARM` per the pre-registered switchback schedule (see `eval/experimental_constants.py.design.switchback_design`).
6. Vector begins ~4-6 weeks of normal roomd work; every task ends with `phd_mem record-task` (thin wrapper TBD; or manually edit JSON sidecars under `~/.roomd/task_records/`).
7. Periodically run `make eval_corpus` (or just `python -m eval.runner`) to update `phd/results/session_metrics.jsonl`.
8. At N≥120 sessions: run final stats + add Phase 2 results table to paper v1.0, replacing `v0.1.md`.

## What's NOT in Phase 1 (per the architecture's deliberate scope)

- The actual longitudinal deployment (that's Phase 2; Vector's daily work IS the experimental unit).
- Cross-team independent replication (Phase 4).
- Cursor / Windsurf / Cline adapters (out of scope per locked architecture).
- LLM-graded `prior_knowledge_recall` with 3-judge κ (Phase 3 hardening; v0.1 paper documents the protocol but no judgments have been collected yet).
- Qwen3-Embedding-8B-MLX swap (Phase 2; we shipped with fastembed BGE-small for portability).
- Production-grade GCMP integration on a real worktree fleet (Phase 3).

## Risk register (current)

- **Letta-server unavailability in Phase 1 smoke.** Documented in the paper as the Letta arm SKIPPED in Phase 1; Phase 2 starts a Docker'd server.
- **Cognee LLM-credential dependency for search.** Add() works; cognify() and graph-based search require LLM credentials. Phase 2 will set `ANTHROPIC_API_KEY` for the duration of the deployment.
- **Sandelin's planned 27-session follow-up.** Not yet appeared (2026-05-25); the pre-registration commit timestamp will lock priority once made.
- **Letta velocity.** Letta is actively shipping (Feb 2026 release). Between Phase 1 and Phase 2 submission, Letta could ship selective inheritance or live cross-worktree query, which would erode the GCMP novelty surface. Mitigation: GCMP is composable atop any MemoryBackend, so if Letta MemFS gets selective inheritance, GCMP still wraps it with the calibrated promotion thresholds and live cross-query rerank that remain unique.
- **Spend headroom.** $471 remaining of $500 cap. Phase 2 will use Anthropic + OpenAI subscription tiers (billed separately); no API key spend expected within Phase 2 itself.

## Final report

**70 tests pass. 0 failures. Phase 1 complete. Ready for Phase 2 kickoff.**

Spend: $0.00 added (cumulative $29.07 ≪ $500 cap).
