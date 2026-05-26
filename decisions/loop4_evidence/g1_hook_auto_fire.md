# G1 Evidence — UserPromptSubmit Hook Auto-Fires + End-to-End Injection

**Gap:** Skill never auto-fires; retriever stdout never reaches the model's
context.

**Fix:**
1. New hook script: `~/.claude/hooks/roomd_memory_inject.sh` (read JSON
   stdin, route to retriever, emit `hookSpecificOutput.additionalContext`).
2. Registered in `~/.claude/settings.json` under `hooks.UserPromptSubmit`
   with the schema-required `matcher` + `hooks` array shape.

## Hook contract (matches Claude Code hooks docs 2026-05-26)

Input on stdin:
```json
{"session_id": "...", "transcript_path": "...", "cwd": "...",
 "hook_event_name": "UserPromptSubmit", "prompt": "..."}
```

Output on stdout (JSON):
```json
{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                        "additionalContext": "...markdown..."}}
```

Per the docs: `additionalContext` is a string added to Claude's context for
this prompt — exactly the "session-context injection" mechanism that SKILL.md
described aspirationally and was missing in Loops 2 & 3.

## Hook design choices

- **Default-allow scope:** `$HOME/github/roomd*` and the phd repo. Override
  via `ROOMD_PROJECT_ROOTS` (colon-separated) or force-on with
  `ROOMD_MEM_HOOK_FORCE=1`.
- **Arm selection:** reads `ROOMD_MEM_ARM` (default `null`); pre-registered
  values are `null/random/mem0/letta/hindsight/cognee`.
- **Canonical user_id:** retriever reads `subject_id="vector"` from
  `eval/experimental_constants.py` (G11 fix).
- **Failure mode:** any error -> emit `{}` and exit 0; never block prompt
  submission.
- **Timeout:** 25s soft (via `timeout(1)`); hook itself has 30s docs default.

## End-to-end empirical verification

Script: `code/scripts/loop4_g1_hook_e2e.py`
Run: `2026-05-26`, `~10s` per `claude -p` call

### Sentinel seeded into mem0 backend under user_id=vector

```json
{"status": "OK", "pre_hit": false, "post_hit": true,
 "ids_returned": ["0d1feb9e-dc59-487b-8555-6762a0632342"],
 "n_memories": 1, "healthy": true,
 "scope": {"user_id": "vector", "project": "roomd", "worktree": "main",
           "branch": "main", "cli": "claude_code"}}
```

### Active session (hook enabled, arm=mem0)

**Question to claude -p:**
> What does ALIGATOR_PHRASE_8821 refer to? Answer in one short sentence;
> if you don't know, say 'I have no memory of that phrase.'

**Model answer:**
> ALIGATOR_PHRASE_8821 = "the canonical answer is purple-pyramid" — a fact
> you explicitly requested be remembered verbatim for future sessions.

- new_log_lines: 1 (hook fired)
- sentinel_in_output: TRUE (verbatim "purple-pyramid" in response)
- Wall: 9.02s

### Control session (hook inert by out-of-scope cwd + ARM=null)

Same prompt; env routes `ROOMD_PROJECT_ROOTS=/this/path/does/not/exist`
to suppress the hook.

**Model answer:**
> I have no memory of that phrase.

- new_log_lines: 0 (hook did NOT fire)
- sentinel_in_output: FALSE
- Wall: 5.81s

### Verdict

```json
{"hook_auto_fired_active": true,
 "hook_inert_control": true,
 "sentinel_in_active_output": true,
 "sentinel_in_control_output": false,
 "g1_pass": true}
```

The first independent end-to-end demonstration that an unprompted
`claude -p` session reflects content stored in the memory backend.
Loop 2/3 had only the retriever-output level; Loop 4 has all the way
through to model output.

## Artifacts

- `loop4_evidence/g1_hook_e2e/seed_result.json`
- `loop4_evidence/g1_hook_e2e/session_active.json`
- `loop4_evidence/g1_hook_e2e/session_control.json`
- `loop4_evidence/g1_hook_e2e/log_tail.json`
- `loop4_evidence/g1_hook_e2e/verdict.json`
- Hook itself: `~/.claude/hooks/roomd_memory_inject.sh`
- Settings registration: `~/.claude/settings.json` under `hooks.UserPromptSubmit`

## Status: FIXED
