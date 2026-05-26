# G9 Evidence — Negative-Sentinel Leak Eliminated

**Gap:** D5 evidence file `walled_check.n_memories_under_walled_uid: -1`.
The Loop-2 HONEST-Mem fix was supposed to make `-1` impossible, but
`Mem0Backend._safe_count_memories` still had three `return -1` paths
and external callers (D5, D4, loop3 investigator c_t4) propagated the
sentinel directly.

## Source-level fix

`code/memory/mem0_backend.py::_safe_count_memories`:

**Before:** 4 paths returning `-1` (uninitialized, TypeError-then-Exception,
v2-Exception, v2-then-legacy-Exception).

**After:** all 4 paths return `0` AND set `self._health.last_error` with a
diagnostic message. Callers that need to distinguish "unknown count" from
"zero stored" inspect `last_error`.

Defense-in-depth: `code/scripts/d5_cross_cli_bridging.py` now also clamps
any negative value it sees from `_safe_count_memories`, recording the raw
value into `walled_check_diagnostics.clamped_negative_count` if it ever
happens (so a future regression cannot silently re-introduce the sentinel).

## Test coverage

Two new pytest invariants in `tests/test_honest_mem_invariants.py`:

1. `test_g9_safe_count_memories_never_returns_negative` — empirically
   forces the uninitialized branch (`backend._m = None`), confirms the
   return is `0` (not `-1`), and confirms `last_error` carries the
   "not initialized" diagnostic.
2. `test_g9_grep_no_negative_sentinel_in_safe_count` — source-level
   regression guard: the literal `return -1` cannot appear in the function.

## Existing tests not broken

The Loop-2 invariant `test_inspect_raises_on_negative_sentinel` still
passes (it directly sets `_health.n_memories=-1` to simulate the
"impossible" condition; inspect() still raises). The Loop-2
`test_mem0_silent_extraction_failure_is_loud` still passes (the
silent-extraction path still flips healthy to False via `_record_error`,
unrelated to `_safe_count_memories`).

## Empirical verification

```
cd phd/code && ./.venv/bin/python -m pytest tests/test_honest_mem_invariants.py -v
============================== 9 passed in 18.03s ==============================
```

## Status: FIXED
