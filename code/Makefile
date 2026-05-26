# PhD Phase 1 — reproducibility Makefile
#
# Targets:
#   smoke          — run the full smoke test (all 6 backends + governance + calibration)
#   precheck       — verify corpus + adapter health (no API calls)
#   adapters_test  — pytest the adapters
#   memory_smoke   — pytest the memory backends (~60s; includes fastembed model fetch)
#   calibration    — pytest PDDC
#   governance     — pytest GCMP
#   eval_test      — pytest eval harness components
#   preregister    — write preregistration/v1.md + print hash for git commit
#   eval_corpus    — run the eval runner against the real roomd corpus (Claude Code only, 30 sessions cap)
#   paper          — render v0.1 paper to markdown + PDF (weasyprint)
#   all            — full smoke + preregister
#   clean          — remove derived state (NOT the venv)

PY := /Users/aiSandbox/github/claude_can_do_anything/distillation/phd/code/.venv/bin/python
ROOT := /Users/aiSandbox/github/claude_can_do_anything/distillation/phd
CODE := $(ROOT)/code

.PHONY: all smoke precheck adapters_test memory_smoke calibration governance eval_test preregister eval_corpus paper clean

all: smoke preregister
	@echo "[Make] all targets complete."

smoke: adapters_test memory_smoke calibration governance eval_test
	@echo "[Make] smoke: all subtests passed."

adapters_test:
	cd $(CODE) && $(PY) -m pytest tests/test_adapters.py -v --tb=short

memory_smoke:
	cd $(CODE) && $(PY) -m pytest tests/test_memory_smoke.py -v --tb=short

calibration:
	cd $(CODE) && $(PY) -m pytest tests/test_calibration.py -v --tb=short

governance:
	cd $(CODE) && $(PY) -m pytest tests/test_governance.py -v --tb=short

eval_test:
	cd $(CODE) && $(PY) -m pytest tests/test_eval.py -v --tb=short

precheck:
	@echo "[precheck] Counting corpus..."
	@find /Users/aiSandbox/.claude/projects -maxdepth 1 -type d -name "*roomd*" | wc -l | xargs -I {} echo "  roomd Claude Code project dirs: {}"
	@find /Users/aiSandbox/.claude/projects -path "*roomd*" -name "*.jsonl" | wc -l | xargs -I {} echo "  roomd Claude Code JSONL files:  {}"
	@find ~/.codex/sessions ~/.codex/archived_sessions -name "*.jsonl" 2>/dev/null | wc -l | xargs -I {} echo "  Codex JSONL files (all):        {}"
	@cd $(CODE) && $(PY) -c "from adapters.claude_code_jsonl import iter_roomd_sessions; print(f'  iter_roomd_sessions yields:     {len(list(iter_roomd_sessions()))} files')"
	@cd $(CODE) && $(PY) -c "from adapters.codex_rollout_jsonl import iter_codex_sessions; print(f'  iter_codex (cwd~roomd) yields:  {len(list(iter_codex_sessions(require_cwd_contains=\"roomd\")))} files')"
	@cd $(CODE) && $(PY) -c "from eval.experimental_constants import freeze_constants_hash; print(f'  Pre-reg hash:                   {freeze_constants_hash()}')"

preregister:
	@cd $(CODE) && $(PY) -m eval.pre_registration
	@echo ""
	@echo "[preregister] Pre-registration written. To lock priority:"
	@echo "    cd $(ROOT) && git init && git add preregistration/v1.md && git commit -m 'PRE-REGISTRATION HASH \$$(cat preregistration/v1.md | grep hash_sha256 | head -1)'"

eval_corpus:
	cd $(CODE) && $(PY) -m eval.runner --max-sessions 30 --no-codex

paper:
	cd $(CODE) && $(PY) ../paper_build.py 2>/dev/null || echo "(paper builder script not yet integrated; see paper/v0.1.md for manual build)"

clean:
	rm -rf $(CODE)/.pytest_cache $(ROOT)/results
	rm -f $(CODE)/fixtures/memory_smoke_summary.json
	@echo "[clean] removed derived state (venv and source preserved)"
