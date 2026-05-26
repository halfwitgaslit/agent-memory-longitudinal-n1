# G7 Evidence — Mem0 Cross-Process Lock Resolved via Subprocess Isolation

**Gap:** `~/.mem0/migrations_qdrant/.lock` persists across processes (and even
across in-process Mem0Backend instances). Loop 2's PASS was a one-process
no-prior-lock run. Phase 2 deployment (many sessions per day, parallel arms)
would deadlock.

## Fix architecture

Two parts:

### 1. `code/memory/mem0_subprocess.py::Mem0SubprocessBackend`

A drop-in replacement for `Mem0Backend` (same `MemoryBackend` interface)
that spawns a short-lived subprocess for each `add`/`search`/`inspect`/
`clear` op. The subprocess constructs a fresh `Mem0Backend`, runs the op,
returns JSON, and exits — releasing the qdrant lock on exit.

Trade-offs:
- **Overhead:** ~200-300ms per call from venv warm-up + fastembed model
  load. Acceptable for n=1 longitudinal evaluation where calls are
  user-initiated and have human-latency budgets.
- **Stable surface:** identical method signatures and return types as
  `Mem0Backend`, so the eval harness can drop in either depending on
  whether it needs concurrency.

### 2. Cross-process file lock in `_mem0_subprocess_worker.py`

A global `fcntl.flock` mutex at `~/.mem0/.phd_mem0_subprocess_lock`,
held for the duration of each worker subprocess. Other workers spin
(0.1s poll) until acquired or the 60s timeout fires.

Why fcntl + per-worker hold (not per-op):
- The qdrant lock is held by the qdrant client across the lifetime of
  the Mem0 instance, not just during a single API call. Releasing the
  global lock between op-init and op-execute would race with another
  worker init.
- 60s timeout surfaces a real deadlock as a `TimeoutError` rather than
  hanging forever — the eval harness can then escalate, retry, or skip.

## Empirical verification

Script: `code/scripts/loop4_g7_concurrent_processes.py`
Run: `2026-05-26`

### Two CONCURRENT processes, each with its own store_dir

Both processes spawned via `multiprocessing.Process`, each invokes
`Mem0SubprocessBackend.add(...).search(...)` independently:

```json
{
  "test": "two_concurrent_processes",
  "n_processes": 2,
  "results": [
    {"slot": "A", "marker": "G7_MARKER_RAINBOW_ALPHA_3719",
     "ids": ["c1c46329-..."], "n_mems": 1, "found_marker": true, "ok": true},
    {"slot": "B", "marker": "G7_MARKER_RAINBOW_BETA_4280",
     "ids": ["4a6199f1-..."], "n_mems": 1, "found_marker": true, "ok": true}
  ],
  "all_ok": true
}
```

### Behavior without the fix (control)

The first iteration of this script — before the `fcntl.flock` was added —
showed `all_ok: false`: slot A's add returned `[]` because slot B's
subprocess was still holding the global `~/.mem0/migrations_qdrant`
lock from its own Mem0Backend init. After adding the fcntl lock both
slots succeed.

## Test-suite hygiene

`tests/conftest.py` autouse fixture clears `~/.mem0/migrations_qdrant/.lock`
before each test, so the pytest suite continues to work for tests that
construct Mem0Backend directly (faster than subprocess for unit tests).

## Artifacts

- `code/memory/mem0_subprocess.py`
- `code/memory/_mem0_subprocess_worker.py`
- `tests/conftest.py`
- `loop4_evidence/g7_concurrent/concurrent_processes.json`

## Status: FIXED
