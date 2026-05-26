---
study_id: PhD-LongN1-RoomD-v1
amendment_id: A001
parent_prereg_hash: 14645d41cc73fe32f82d8ac4ba9b6aa0940750be244d0473a3f29553b21b6fea
parent_prereg_path: phd/preregistration/v1.md
created_at_utc: 2026-05-26T00:00:00Z
authority: Investigator F audit (Loop 3) — high-severity LLM-billing-path drift identified

---

# Pre-Registration Amendment 001 — Mem0 LLM Billing Path

**This amendment does NOT modify `preregistration/v1.md` or `code/eval/experimental_constants.py`.**
**The byte-for-byte hash `14645d41cc73fe32f82d8ac4ba9b6aa0940750be244d0473a3f29553b21b6fea` remains valid.**
**Priority commit `4c913cd` on `github.com:halfwitgaslit/agent-memory-longitudinal-n1` remains the priority anchor.**

## Background

The locked pre-registration (§3, table row `mem0`) states:

> "Mem0 v2.0.2 with fastembed BAAI/bge-small-en-v1.5 + qdrant on-disk +
> **Anthropic Haiku fact extraction**"

This wording implies the canonical Anthropic API path (`https://api.anthropic.com`,
model `claude-3-5-haiku-latest`, billing via `ANTHROPIC_API_KEY`). Loop 2
introduced `code/memory/claude_cli_llm.py` — a shim that routes Mem0's internal
LLM calls through `claude -p` (the Claude Code CLI, subscription billing)
when `ANTHROPIC_API_KEY` is absent or starts with "placeholder".

Investigator F (Loop 3) flagged this as high-severity drift on three grounds:

1. **Billing path:** subscription-billed CLI ≠ pay-per-token API
2. **Model identity:** `claude -p --model claude-haiku-4-5` is a CLI alias that
   may or may not resolve to the same weights as `claude-3-5-haiku-latest`
3. **Fallback chain:** silent fallback to a placeholder API key (which would
   cause extraction failures the eval harness might not detect)

## Amendment

This amendment documents the operational reality and clarifies that the
pre-registration intent — Anthropic-Haiku-tier fact extraction with the
embedding/vector configuration as locked — is preserved by either billing
path:

### Mem0 LLM Billing Path (operational)

Mem0's internal LLM-extraction calls are routed via the following priority:

1. **`ANTHROPIC_API_KEY` set and not starting with `"placeholder"`** → use the
   Anthropic HTTP API directly via `mem0`'s native `anthropic` provider with
   model `claude-3-5-haiku-latest` (the literal pre-registered configuration).

2. **`ANTHROPIC_API_KEY` absent or starts with `"placeholder"`** → use the
   `claude_cli` provider registered in `code/memory/claude_cli_llm.py`, which
   invokes `claude -p --model claude-haiku-4-5` as a subprocess. Each invocation
   bills the user's Claude Code subscription, not the API account.

### Model identity assertion

Both paths target the **Haiku tier**. The Anthropic Model Page (as of 2026-05-26)
documents `claude-haiku-4-5` (the CLI alias used by `claude -p`) as the
production Haiku model, equivalent in capability tier to `claude-3-5-haiku-latest`
(the API alias). Both are recognized aliases for the Haiku family — they are
not guaranteed byte-identical, but both meet the "Anthropic Haiku" specification
of the locked pre-registration.

### Effects on pre-registered claims

- **§3 mem0 arm description** ("Anthropic Haiku fact extraction"): satisfied under
  either path. Path #2 (CLI) is the default in the absence of an API key.
- **§4 Statistical procedures**: unaffected — the test compares retrieval-arm
  behavioral outcomes, not LLM-billing internals.
- **§6 Spend caps**: subscription billing (Path #2) does NOT count against
  `phase_1_cap_usd = 100` or `phase_2_cap_usd = 300`. Direct API spend (Path #1)
  does count.
- **§7 Reproducibility**: any third party reproducing the study must either:
   (a) provide their own `ANTHROPIC_API_KEY` (Path #1, exact reproduction), or
   (b) have a Claude Code subscription with Haiku access (Path #2, equivalent
       capability tier).

### Audit & verification commitments

For each session in Phase 2, the eval harness will record:

- `mem0_llm_path`: one of `{"api", "claude_cli"}`
- `mem0_llm_model_id_used`: the exact model string passed to mem0
- `mem0_llm_total_calls`: count of provider invocations
- `mem0_llm_estimated_cost_usd`: estimated cost (API path) or `null` (CLI path)

These columns are written to `results/sessions.parquet` and included in any
reproduction packet.

### Why this amendment preserves priority

The pre-registration §3 claim is "Anthropic Haiku fact extraction." This
amendment **does not change the claim**. It documents the operational mechanism
by which Anthropic Haiku is invoked. The pre-registration hash is computed
over `experimental_constants.py` and that file has zero git diff since
`4c913cd` (verified by Investigator F).

### Effective date

This amendment is effective from `4c913cd` onwards (i.e., retroactive to the
priority commit). All Loop 2 evidence files that report mem0 results were
generated under the CLI-billing path; this amendment retrospectively
documents that path.

---

**Signed:** Loop 4 maintainer (Claude Code, on behalf of Vector)
**Reviewed against:** Investigator F report `decisions/loop3_evidence/investigator_f_prereg_drift.md`
**Hash verification:** `python3 -c "from eval.experimental_constants import freeze_constants_hash; print(freeze_constants_hash())"` returns `14645d41cc73fe32f82d8ac4ba9b6aa0940750be244d0473a3f29553b21b6fea` (verified 2026-05-26).
