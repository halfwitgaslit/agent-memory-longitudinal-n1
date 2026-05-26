# G4 Evidence — Letta Backend: HONEST-Mem Invariants Restored + Model Discovery

**Gap (Loop 3):**
1. `agents.create()` 404'd because `LettaBackend` hard-coded
   `model="openai/gpt-4o-mini"` + `embedding="openai/text-embedding-3-small"`,
   which the local Letta server (`roomd-letta` container) does NOT have
   registered.
2. After 5 failed `add()` calls, `inspect()` returned
   `healthy=True, n_errors=8, last_error=None` — a HONEST-Mem invariant
   violation that would have let the eval harness treat zero retrievals as
   a valid Letta-arm signal.

## Fix

### Part 1: discover model handles from the live server

`code/memory/letta_backend.py::_discover_model_handles()` queries
`http://<base_url>/v1/models/` (LLMs) and `/v1/models/embedding`
(embeddings) at agent-creation time and uses the first available handle
of each type. The local Letta `roomd-letta` container exposes
`letta/letta-free` for both — agent creation now succeeds.

Overridable via:
- `config.model` / `config.embedding`
- `$ROOMD_LETTA_MODEL` / `$ROOMD_LETTA_EMBEDDING`

### Part 2: HONEST-Mem path goes through `_record_error`

`_ensure_agent` now calls `self._record_error("letta.ensure_agent", ...)`
on failure, which centrally increments `n_errors`, sets `last_error`,
flips `healthy=False`. The Loop-3 direct-write-to-error_message
pattern is gone.

Same path is taken by `add()` and `search()` on failure — they were
already calling `_record_error`, but their precondition check
(`if not healthy: return []`) used to swallow the cause silently.
With Part 1 in place, agent creation no longer fails immediately, so
substantive add failures (server 500 from the inference.letta.com
embedding endpoint) DO surface as real `n_errors > 0` increments.

### Part 3: model handles propagated even when re-using an existing agent

When `agents.list(name=...)` returns a prior agent, we now also stamp
`extra["agent_model"]` / `extra["agent_embedding"]` from the returned
agent object so the diagnostic record is complete.

## Empirical verification

Script: `code/scripts/loop4_g4_letta_e2e.py`
Run: `2026-05-26`

### Scenario A — live `roomd-letta` container

The local Letta container's `letta/letta-free` model handle proxies to
`https://inference.letta.com/v1/embeddings`, which returns 404 without
a paid account. So `passages.create()` fails with `InternalServerError:
500`. Critically, this failure is now HONEST:

```json
{
  "post_status": "FAILURE_BUT_HONEST",
  "healthy_post_add": false,
  "n_errors_post_add": 2,
  "last_error": "letta.add: InternalServerError: Error code: 500 - {'detail': 'An unknown error occurred'}",
  "invariants_breakdown": {
    "healthy_after_failure_is_False": true,
    "n_errors_gt_zero": true,
    "last_error_populated": true,
    "agent_model_discovered": true
  },
  "honest_mem_invariants_satisfied": true
}
```

The Phase 2 eval harness will treat Letta-arm sessions as SKIPPED-UNHEALTHY
on this substrate (per `architecture/v1.md` §4.2) — NOT as "Letta retrieved
zero memories" (the bug we were avoiding).

### Scenario B — force failure (bogus base_url)

Sends `base_url="http://localhost:1"` so init itself fails. After `add()`:

```json
{
  "invariants": {
    "healthy_after_failure_is_False": true,
    "n_errors_gt_zero_or_init_unhealthy": true,
    "last_error_populated_or_init_unhealthy": true,
    "no_ids_returned": true
  },
  "all_invariants_pass": true
}
```

### Verdict

```json
{"g4_pass": true,
 "details": {"live_status": "FAILED",
             "live_invariants": {...all true...},
             "force_failure_invariants": {...all true...}}}
```

## Artifacts

- `loop4_evidence/g4_letta/scenario_live_server.json`
- `loop4_evidence/g4_letta/scenario_live_server_invariants.json`
- `loop4_evidence/g4_letta/scenario_force_failure.json`
- `loop4_evidence/g4_letta/verdict.json`

## Status: FIXED

(Letta arm is degraded — substrate inference service unreachable from
the offline env — but degradation is HONEST. Phase 2 will need either
a paid inference.letta.com account OR a different local LLM/embedding
stack registered with the Letta server. This is a substrate-availability
question, not a code-correctness question.)
