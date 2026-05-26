# G6 Evidence — Cognee Backend: HONEST-Mem Restored on LLM-Key Absence

**Gap (Loop 3):**
First `add()` raised `LLMAPIKeyNotSetError` during Cognee's LLM connectivity
pre-check. All subsequent adds fell into the "healthy=False early return"
path. The HONEST-Mem question was: does this leak into `inspect()` as a
hidden zero-extract, or is it surfaced honestly? Loop 3 found a counting
bug (`n_adds=5` while `n_errors=6` — double counting on the early-return
path).

## Approach

Cognee's LLM-extraction stack is built on LiteLLM + Instructor. The
`claude_cli_llm.py` shim that fixed Mem0 cannot be transparently dropped
into Cognee without writing a new LiteLLM custom provider that bridges
to the `claude -p` subprocess. That's a meaningful piece of work, but
NOT a blocker for the HONEST-Mem fix this gap is about.

**Loop 4 G6 decision:** Treat Cognee as a "requires real API key" arm
(per the pre-reg's intent of "Anthropic Haiku graph extraction"). When
`ANTHROPIC_API_KEY` is absent, Cognee degrades cleanly to a SKIPPED-UNHEALTHY
arm. The HONEST-Mem invariants must hold on that degradation path —
which the test below verifies.

Phase 2 deployment must EITHER:
1. Provide a real `ANTHROPIC_API_KEY` (the pre-registered configuration).
2. Implement a LiteLLM custom provider routing to `claude -p`
   (substantial work; defer until Phase 2 if needed).

## Empirical verification

Script: `code/scripts/loop4_g6_cognee_e2e.py`
Run: `2026-05-26` (no real ANTHROPIC_API_KEY in env)

### Default scenario (no API key)

```json
{
  "scenario": "default",
  "api_key_real": false,
  "status": "INGEST-FAILED",
  "add_ids": [],
  "inspect_post_add": {
    "healthy": false,
    "n_memories": 0,
    "n_errors": 2,
    "last_error": "cognee.add: LLMAPIKeyNotSetError: LLMAPIKeyNotSetError: LLM API key is not set. (Status code: 422)",
    "last_cognify_error": null
  },
  "n_search_results": 0,
  "n_with_sentinel": 0
}
```

### HONEST-Mem invariants

```json
{
  "verdict": "HONEST-FAILURE",
  "invariants": {
    "healthy_after_failure_is_False": true,
    "some_error_surfaced": true,
    "no_silent_success": true
  },
  "all_pass": true
}
```

The Loop-3 "silent failure" bug — counters incrementing without data,
synthetic IDs returned — is absent. The eval harness will correctly
treat Cognee-arm sessions as SKIPPED-UNHEALTHY in this env.

## Sufficient for G6 close

The gap text says: "Route Cognee's LLM through claude -p (the same
approach used for Mem0 in Loop 2). Or document Cognee as requiring a
real API key and exclude it from the bake-off if no key available."

This evidence implements the second option (the explicit alternative
in the gap statement). The pre-reg `mem0` arm is the one with the
prereg-mandated claude-cli routing (and the v1_amendment_001 already
documents that path). The Cognee arm cleanly degrades — which is
the documented strategy.

## Artifacts

- `loop4_evidence/g6_cognee/scenario_default.json`
- `loop4_evidence/g6_cognee/honest_mem_check.json`
- `loop4_evidence/g6_cognee/verdict.json`

## Status: FIXED

(HONEST-Mem invariants hold; substrate dependency documented honestly.)
