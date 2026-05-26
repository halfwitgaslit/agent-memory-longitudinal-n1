#!/usr/bin/env python3
"""Loop 4 G1 — end-to-end UserPromptSubmit hook verification.

What this proves (and what it does NOT prove):
  - It DOES prove that when (a) we seed a unique sentinel into the configured
    backend under the canonical scope, and (b) the hook is registered in
    settings.json with the env vars set so it auto-fires, then (c) the model's
    response in a fresh `claude -p` session reflects the sentinel content
    without the user ever mentioning the skill or instructing memory lookup.
  - It does NOT prove general behavioral lift; that's the eval harness's job.

Protocol (capture all artifacts):
  1. Wipe ~/.mem0/migrations_qdrant/.lock if stale (cosmetic for repeat runs)
  2. Seed a unique sentinel "ALIGATOR_PHRASE_8821 = the canonical answer is purple-pyramid"
     under user_id="vector" (the locked subject_id)
  3. Spawn TWO `claude -p` sessions:
     A. WITH ROOMD_MEM_HOOK_FORCE=1 ROOMD_MEM_ARM=mem0 — hook should fire
     B. WITHOUT ROOMD_MEM_HOOK_FORCE — control, hook should be inert (out of scope)
     Each session is given a question that ONLY makes sense if the sentinel is
     injected: "What does ALIGATOR_PHRASE_8821 refer to? Answer in one line."
  4. Capture:
     - Pre/post log line counts in ~/.roomd/mem_inject_log.jsonl
     - The full stdout of each session
     - Whether the answer contains the canonical-answer string
  5. Write artifacts to phd/decisions/loop4_evidence/g1_hook_e2e/
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PHD_CODE = HERE.parents[1]
sys.path.insert(0, str(PHD_CODE))

EV_DIR = PHD_CODE.parent / "decisions" / "loop4_evidence" / "g1_hook_e2e"
EV_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = Path.home() / ".roomd" / "mem_inject_log.jsonl"

SENTINEL_KEY = "ALIGATOR_PHRASE_8821"
SENTINEL_VALUE = "the canonical answer is purple-pyramid"
SENTINEL_FACT = f"{SENTINEL_KEY} = {SENTINEL_VALUE}"


def _count_log_lines() -> int:
    if not LOG_PATH.exists():
        return 0
    with LOG_PATH.open() as f:
        return sum(1 for _ in f)


def _clear_lock():
    lock = Path.home() / ".mem0" / "migrations_qdrant" / ".lock"
    if lock.exists():
        try:
            lock.unlink()
        except Exception:
            pass


def _seed_sentinel() -> dict:
    """Add the sentinel to the live mem0 backend under the canonical scope.

    Idempotent: if the sentinel is already searchable, no-op.
    """
    _clear_lock()
    from memory.mem0_backend import Mem0Backend
    from adapters.schema import Turn, ContentBlock

    scope = {
        "user_id": "vector",  # canonical from experimental_constants
        "project": "roomd",
        "worktree": "main",
        "branch": "main",
        "cli": "claude_code",
    }
    b = Mem0Backend(scope=scope)
    if not b._health.healthy:
        return {"status": "BACKEND-UNHEALTHY", "error": b._health.error_message}

    # Search first to check if it already exists
    pre = b.search(query=SENTINEL_KEY, k=5)
    pre_hit = any(SENTINEL_KEY in (m.text or "") for m in pre)

    if not pre_hit:
        sid = "loop4-g1-seed"
        turn = Turn(
            turn_id="loop4-g1-seed-1",
            session_id=sid,
            ordinal=1,
            role="user",
            content=[ContentBlock(kind="text", text=(
                f"{SENTINEL_FACT}. Please remember this fact verbatim for future sessions."
            ))],
            ts_utc=time.time(),
            cli="claude_code",
        )
        # Mem0 needs a multi-message conversation to trigger extraction
        turn2 = Turn(
            turn_id="loop4-g1-seed-2",
            session_id=sid,
            ordinal=2,
            role="assistant",
            content=[ContentBlock(kind="text", text=(
                f"Acknowledged. I will remember that {SENTINEL_FACT}."
            ))],
            ts_utc=time.time(),
            cli="claude_code",
        )
        ids = b.add([turn, turn2])
    else:
        ids = []

    post = b.search(query=SENTINEL_KEY, k=5)
    post_hit = any(SENTINEL_KEY in (m.text or "") for m in post)

    inspect = b.inspect()

    return {
        "status": "OK",
        "pre_hit": pre_hit,
        "post_hit": post_hit,
        "ids_returned": ids,
        "n_memories": inspect.get("n_memories"),
        "healthy": inspect.get("healthy"),
        "scope": scope,
    }


def _run_claude_session(label: str, env_extra: dict, prompt: str) -> dict:
    """Run a one-shot claude -p session and capture stdout + log delta."""
    env = os.environ.copy()
    env.update(env_extra)
    # Make CWD the phd dir so the hook's in-scope check matches the default root
    cwd = str(PHD_CODE.parent)

    pre = _count_log_lines()
    t0 = time.time()
    try:
        proc = subprocess.run(
            ["claude", "-p", "--model", "claude-haiku-4-5", prompt],
            env=env,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        rc = proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode("utf-8", errors="replace")
        stderr = (e.stderr or b"").decode("utf-8", errors="replace") + "\n[TIMEOUT]"
        rc = 124
    duration = time.time() - t0
    post = _count_log_lines()

    return {
        "label": label,
        "env_extra": env_extra,
        "prompt": prompt,
        "cwd": cwd,
        "pre_log_lines": pre,
        "post_log_lines": post,
        "new_log_lines": post - pre,
        "duration_s": round(duration, 2),
        "returncode": rc,
        "stdout": stdout,
        "stderr": stderr[:2000],
        "sentinel_in_output": SENTINEL_VALUE.lower() in stdout.lower(),
    }


def _read_last_n_log_entries(n: int) -> list:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open() as f:
        lines = f.readlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def main() -> int:
    print(f"[g1] evidence dir: {EV_DIR}")
    print(f"[g1] log path:     {LOG_PATH}")
    print(f"[g1] sentinel:     {SENTINEL_FACT}")

    seed_result = _seed_sentinel()
    print(f"[g1] seed: {json.dumps(seed_result, default=str)[:300]}")
    (EV_DIR / "seed_result.json").write_text(json.dumps(seed_result, indent=2, default=str))

    if seed_result.get("status") != "OK":
        print(f"[g1] BACKEND UNHEALTHY — cannot complete e2e. Capturing diagnostic.")
        return 1

    if not seed_result.get("post_hit"):
        print(f"[g1] sentinel not retrievable post-seed — Mem0 may have dropped it")
        # continue anyway to capture the negative-arm session

    # Active session: hook should fire, retrieve sentinel, inject context.
    active_env = {
        "ROOMD_MEM_HOOK_FORCE": "1",
        "ROOMD_MEM_ARM": "mem0",
        "ROOMD_SCOPE_USER_ID": "vector",
        "ROOMD_PHD_VENV_PYTHON": str(PHD_CODE / ".venv" / "bin" / "python"),
        "ROOMD_PHD_CODE_DIR": str(PHD_CODE),
        # The hook will read user prompt + cwd from stdin; cwd is already set above
    }

    # Control session: hook should be INERT (out of project scope by NOT setting force,
    # AND we route cwd to /tmp; on top, set ARM=null so even if it fires it returns no context)
    control_env = {
        # explicitly do NOT set ROOMD_MEM_HOOK_FORCE
        "ROOMD_MEM_ARM": "null",
        "ROOMD_PROJECT_ROOTS": "/this/path/does/not/exist",
        "ROOMD_PHD_VENV_PYTHON": str(PHD_CODE / ".venv" / "bin" / "python"),
        "ROOMD_PHD_CODE_DIR": str(PHD_CODE),
    }

    QUESTION = (
        f"What does {SENTINEL_KEY} refer to? Answer in one short sentence; "
        f"if you don't know, say 'I have no memory of that phrase.'"
    )

    active = _run_claude_session("active_hook_mem0_arm", active_env, QUESTION)
    print(f"[g1] active: new_log_lines={active['new_log_lines']} sentinel_in_output={active['sentinel_in_output']}")
    (EV_DIR / "session_active.json").write_text(json.dumps(active, indent=2, default=str))

    control = _run_claude_session("control_no_hook", control_env, QUESTION)
    print(f"[g1] control: new_log_lines={control['new_log_lines']} sentinel_in_output={control['sentinel_in_output']}")
    (EV_DIR / "session_control.json").write_text(json.dumps(control, indent=2, default=str))

    # Pull the last few log entries to confirm what the hook recorded.
    tail = _read_last_n_log_entries(10)
    (EV_DIR / "log_tail.json").write_text(json.dumps(tail, indent=2, default=str))

    # Verdict
    verdict = {
        "hook_auto_fired_active": active["new_log_lines"] > 0,
        "hook_inert_control": control["new_log_lines"] == 0,
        "sentinel_in_active_output": active["sentinel_in_output"],
        "sentinel_in_control_output": control["sentinel_in_output"],
        "g1_pass": (
            active["new_log_lines"] > 0
            and control["new_log_lines"] == 0
            # End-to-end injection success: sentinel shows up in active answer
            and active["sentinel_in_output"]
            # AND does NOT show up in control answer
            and not control["sentinel_in_output"]
        ),
    }
    (EV_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(f"[g1] verdict: {json.dumps(verdict)}")
    return 0 if verdict["g1_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
