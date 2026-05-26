# G11 Evidence — Canonical user_id Fix

**Gap:** Skill scope `user_id` mismatch with seeded data — `retriever.py`
defaulted `--scope-user-id` to `$USER` (`aiSandbox`), but data is seeded under
`user_id='vector'` (the pre-registered canonical `subject_id`).

**Fix:** `retriever.py:_canonical_subject_id()` now reads
`EXPERIMENTAL_CONSTANTS["subject"]["subject_id"]` from the locked
`code/eval/experimental_constants.py`. The argparse default is also
overridable via `ROOMD_SCOPE_USER_ID` for tests.

## Before (Loop 3 / Investigator B)

```python
# Line 96 (pre-fix):
ap.add_argument(
    "--scope-user-id", default=os.environ.get("USER", "vector")
)
```

On Vector's machine `$USER=aiSandbox`. Sentinel test (Loop 3): wrong scope -> 0
results. Right scope (--scope-user-id vector) -> sentinel retrieved.

## After (Loop 4)

```python
def _canonical_subject_id() -> str:
    try:
        from eval.experimental_constants import EXPERIMENTAL_CONSTANTS
        return str(EXPERIMENTAL_CONSTANTS["subject"]["subject_id"])
    except Exception:
        return "vector"

ap.add_argument(
    "--scope-user-id",
    default=os.environ.get("ROOMD_SCOPE_USER_ID", _canonical_subject_id()),
)
```

## Empirical verification

Command:
```
cd phd/code && ./.venv/bin/python injection/claude_code_skill/retriever.py --arm null --query "anything"
```

The argparse default resolves to `vector` (verified programmatically). The
canonical constant lookup returns `"vector"`.

Both the in-repo copy at
`code/injection/claude_code_skill/retriever.py` and the installed copy at
`~/.claude/skills/roomd-memory-retrieval/retriever.py` were updated and `diff`
confirms they are byte-identical.

## Effects on other gaps

- G1 (UserPromptSubmit hook) — will invoke retriever with this default, so the
  hook will retrieve data seeded under `user_id=vector` by Phase 2 seeding.
- G8 (D2/D5 rerun) — same canonical user_id will be used.
- G12 — orthogonal (LLM billing path, not user_id).

## Status: FIXED
