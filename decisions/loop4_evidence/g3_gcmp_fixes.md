# G3 Evidence — GCMP Denominator + Inheritance Persistence + Honest Label

**Gap (Loop 3 Investigator D):**
1. **Denominator bug:** `is_eligible()` computed
   `hit_rate = hit_count / (hit_count + support_count)`, conflating two
   distinct counters. The 0.7 threshold effectively required
   `hit_count > 2.33 × support_count` — far stricter than intended.
2. **fork_worktree throwaway dict:** inherited IDs were written to
   `inspect().get("extra", {})["_pending_inheritance"]`, but `inspect()`
   builds a fresh dict each call, so the IDs were silently discarded.
3. **False "calibrated" claim:** code comments said
   "calibrated against the roomd corpus" but no calibration code exists.

## Fix

### 1. Hit-rate formula

`code/governance/cross_worktree.py::PromotionPolicy.is_eligible()`:

**Before:**
```python
denom = max(1, m.hit_count + m.support_count)
hit_rate = m.hit_count / denom
```

**After:**
```python
denom = max(1, m.support_count)
hit_rate = m.hit_count / denom
```

Now `hit_rate = hits / opportunities`, where `support_count` is the
number of opportunities (sessions that referenced the memory).

### 2. Inheritance persistence

`WorktreeMemoryView` gains three fields:
- `inherited_memory_ids: List[str]` (durable storage)
- `inherited_from: Optional[str]`
- `fork_ts_utc: Optional[float]`

`GCMPManager.fork_worktree()` now writes to these fields directly:

**Before:**
```python
child_view.backend.inspect().get("extra", {})["_pending_inheritance"] = [...]
# inspect() returned a throwaway dict; IDs lost
```

**After:**
```python
child_view.inherited_memory_ids = [m.memory_id for m in inherited]
child_view.inherited_from = ctx.parent_worktree
child_view.fork_ts_utc = ctx.fork_ts_utc
```

`WorktreeMemoryView.inspect()` now surfaces `inherited_memory_ids`
and friends into its own return dict so external callers can verify
persistence.

### 3. Honest comment

Module docstring and inline comments updated to remove the "calibrated
against the roomd corpus" claim. The defaults are now honestly labeled
as hand-tuned, with a forward note that Phase 2 will calibrate against
promotion-event logs.

## Test coverage

Three new pytest invariants in `tests/test_governance.py`:

1. `test_g3_hit_rate_formula_uses_support_as_denominator` — a memory with
   `support=5, hit=8` would FAIL the old `0.7` threshold (8/13 = 0.615
   < 0.7) but PASSES the new formula (8/5 = 1.6 > 0.7).
2. `test_g3_fork_worktree_persists_inherited_ids` — after `fork_worktree`,
   `child.inherited_memory_ids` is a real list, `inherited_from` is set,
   `fork_ts_utc` is set, and `child.inspect()` surfaces them.
3. `test_g3_default_promotion_policy_label_is_truthful` — source-grep
   guard against re-introducing the "calibrated against the roomd
   corpus" wording near the DEFAULT_*_POLICY definitions.

Plus the existing `test_promotion_policy_thresholds` still passes
because its test fixtures (support=4, hit=10) clear the new formula too.

## Empirical verification

```
cd phd/code && ./.venv/bin/python -m pytest tests/test_governance.py -v
============================== 11 passed in 0.04s ==============================
```

## Status: FIXED
