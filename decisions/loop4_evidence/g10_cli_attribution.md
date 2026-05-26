# G10 Evidence — CLI Attribution Round-Trips Through Bridge Mode

**Gap:** Investigator C found that memories retrieved under `bridge_scope`
(scope with `cli` key omitted) carry NO originating-CLI metadata. Eval
harness could not tell which CLI ingested which memory.

## Fix

`code/memory/mem0_backend.py`:

- **`add()`**: passes a `metadata` kwarg to `mem0.Memory.add()` containing:
  - `_origin_cli` — the originating CLI from `Turn.cli` (`"claude_code"` or `"codex"`)
  - `_origin_scope_user_id`, `_origin_scope_project`, `_origin_scope_worktree`,
    `_origin_scope_branch`, `_origin_scope_cli_at_ingest`
  - `_phd_loop4_ingest_ts_utc`
- **`search()`**: lifts those keys from the raw mem0 result into
  `Memory.metadata` so downstream callers don't have to dig through `raw`.

Mem0 v2.0.2's `Memory.add()` signature already supports `metadata: Optional[Dict[str, Any]]`,
so no surface change was required on the Mem0 side.

## Empirical verification

Script: `code/scripts/loop4_g10_origin_cli_roundtrip.py`
Run: `2026-05-26`

### Bridge scope used (NO `cli` key):

```json
{"user_id": "vector", "project": "roomd", "worktree": "main", "branch": "main"}
```

### Two seeds with different originating CLI:

1. `LOOP4_G10_CC_PORCUPINE_5471` — added with `Turn.cli="claude_code"`, scope=bridge
2. `LOOP4_G10_CX_ZEPPELIN_9938` — added with `Turn.cli="codex"`, scope=bridge

### Retrieval under bridge_scope:

```json
{
  "origin_cli_observed": {"cc": "claude_code", "cx": "codex"},
  "verdict": {"cc_origin_cli_correct": true, "cx_origin_cli_correct": true,
              "g10_pass": true}
}
```

Both markers retrieved under bridge_scope; both metadata-tagged with the
correct originating CLI; eval harness can now attribute memories by their
ingest-time CLI even when the storage partition is shared.

## Artifacts

- `loop4_evidence/g10_origin_cli/seed_cc.json`
- `loop4_evidence/g10_origin_cli/seed_cx.json`
- `loop4_evidence/g10_origin_cli/search_summary.json`

## Status: FIXED
