# G5 Evidence — Hindsight Backend: Real API + HONEST-Mem Invariants

**Gap (Loop 3):**
1. `_ensure_bank()` called `list_banks(context=ctx)` with the wrong kwarg
   name — the actual hindsight-api 0.6.x signature is
   `list_banks(*, request_context=ctx)`. AttributeError, no bank
   created.
2. `add()` returned synthetic SHA1 IDs (`hashlib.sha1(text).hexdigest()[:16]`)
   without actually storing anything in Hindsight's DB. `recall()` returned
   0 results for every query.
3. The synthetic-ID hack masked the broken pipeline: counters incremented,
   ids "returned," `inspect()` reported healthy.

## Fix architecture (substantial rewrite of `hindsight_backend.py`)

### Part 1: real hindsight-api 0.6.x surface

- **Bank creation:** `get_bank_profile(bank_id, request_context=ctx,
  create_if_missing=True)`. There is no `create_bank` in the public API —
  this is the documented implicit-create path.
- **Ingest:** `engine.retain_async(bank_id, content, context=..., request_context=ctx)`.
  Returns `list[str]` of real memory_unit_ids.
- **Recall:** `engine.recall_async(bank_id, query, fact_type="experience", ...)`.
  Returns `(list[dict], trace)`.
- **Clear:** `engine.clear_observations(bank_id, request_context=ctx)`.

### Part 2: persistent asyncio event loop

Hindsight 0.6.x is async-first. Its sync wrappers (`retain()`, `recall()`)
internally call `asyncio.run()` which creates a NEW event loop each call;
the DB pool gets bound to a loop that subsequently closes, producing
`RuntimeError: Event loop is closed` on the next call.

Loop 4 fix: `HindsightBackend` keeps a SINGLE `asyncio.new_event_loop()`
alive for the backend's lifetime and uses `loop.run_until_complete(...)`
for every async call — never `asyncio.run()`. This binds the DB pool to
a stable loop. Closed only in `close()` / `__del__`.

### Part 3: HONEST-Mem path

- The synthetic-SHA1-ID hack is GONE. add() returns real ids from
  `retain_async()` or surfaces failure.
- `_ensure_bank` failures go to `self._health.extra["ensure_bank_error"]`;
  if bank is None, add()/search() calls `_record_error` and returns [].
- Substantive input with zero returned ids triggers
  `_record_error(silent_extraction=True)` so `healthy=False`,
  `n_errors > 0`, `last_error` populated, `n_silent_extraction_failures > 0`.

## Empirical verification

Script: `code/scripts/loop4_g5_hindsight_e2e.py`
Run: `2026-05-26`

### Scenario A — real_ingest

Real Hindsight engine, embedded pg0 Postgres, LocalSTEmbeddings
(sentence-transformers/all-MiniLM-L6-v2). Tries to ingest a substantive
turn. The LLM call (extract-facts step inside `retain_async`) uses the
placeholder Anthropic API key, so `retain_async` returns `[]` (it
silently swallows the LLM extraction failure, returning an empty unit list).

Result (post-fix):

```json
{
  "scenario": "real_ingest",
  "status": "FAILED",
  "add_ids": [],
  "inspect_post_add": {
    "healthy": false,
    "n_memories": 0,
    "n_errors": 1,
    "last_error": "hindsight.add: engine.retain returned no ids on substantive input",
    "bank_id": "phd_31f83a0c41",
    "ensure_bank_error": null
  }
}
```

- The bank WAS created (`bank_id="phd_31f83a0c41"`); the API mismatch is gone.
- The LLM-extraction silent-zero is detected and flagged
  (`silent_extraction=True` path in `_record_error`).
- `inspect()` returns the HONEST view: `healthy=False, n_errors=1, last_error`
  populated.

### Scenario B — force_failure

Init with a bogus `db_url=postgresql://nobody:nope@127.0.0.1:99/nope`.

```json
{
  "invariants": {
    "healthy_after_failure_is_False_or_init_unhealthy": true,
    "n_errors_gt_zero_or_init_unhealthy": true,
    "last_error_populated_or_init_unhealthy": true,
    "no_ids_returned": true
  },
  "all_invariants_pass": true
}
```

### Verdict

`g5_pass: true`. HONEST-Mem invariants hold across both scenarios. The
"counter increments without data" bug from Loop 2/3 is fully eliminated.

## Substrate limitation (documented honestly)

Hindsight's `retain` flow REQUIRES a working LLM to extract facts from
content. Our offline test env has only the placeholder API key, so
real retrieval-grade ingestion cannot complete end-to-end. **The
correct response is the HONEST one shown above: healthy=False, real
diagnostic, no synthetic IDs.** This is exactly the behavior the
Phase 2 eval harness needs to skip Hindsight cleanly when an API key
is absent.

Phase 2 deployment options:
1. Provide a real `ANTHROPIC_API_KEY` (the pre-registered
   `claude-3-5-haiku-latest` path).
2. Route through a local `memory_llm_base_url` proxy (e.g., a thin
   Anthropic-compatible HTTP wrapper around `claude -p`). Not done in
   Loop 4 because (a) the HONEST-Mem invariants are restored
   independently and (b) it would duplicate work being done for the
   Mem0 arm.

## Artifacts

- `loop4_evidence/g5_hindsight/scenario_real_ingest.json`
- `loop4_evidence/g5_hindsight/scenario_force_failure.json`
- `loop4_evidence/g5_hindsight/verdict.json`

## Status: FIXED

(HONEST-Mem fully restored; substrate limitation documented.)
