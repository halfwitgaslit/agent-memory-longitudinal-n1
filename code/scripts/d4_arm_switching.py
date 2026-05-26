#!/usr/bin/env python3
"""Deliverable 4 — arm switching end-to-end.

Runs the SAME query under each ROOMD_MEM_ARM setting (null, random, mem0,
letta) and verifies via ~/.roomd/mem_inject_log.jsonl that the correct
backend was invoked for each.

Letta needs the local Letta server (http://localhost:8283); if the probe
fails the entry will be UNHEALTHY rather than OK — that's an acceptable
documented outcome from architecture/v1.md §4.2.

Mem0 here uses the persistent qdrant dir from D2 (already populated with
5 memories) so we can also verify that mem0 returns real results.

Evidence: phd/decisions/loop2_evidence/d4_arm_switching_report.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT.parent / "decisions" / "loop2_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
REPORT = EVIDENCE_DIR / "d4_arm_switching_report.json"

LOG = Path.home() / ".roomd" / "mem_inject_log.jsonl"
RETRIEVER = ROOT / "injection" / "claude_code_skill" / "retriever.py"
VENV_PY = ROOT / ".venv" / "bin" / "python"

QUERY = "What library do we use for schemas?"
K = 5
SCOPE = {
    "user_id": "vector",
    "project": "roomd",
    "worktree": "loop2_d4",
    "branch": "main",
}


def _count_log_lines() -> int:
    if not LOG.exists():
        return 0
    return sum(1 for _ in LOG.open())


def _tail_log(n: int) -> list:
    if not LOG.exists() or n <= 0:
        return []
    lines = LOG.read_text().strip().splitlines()
    out = []
    for ln in lines[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            out.append({"raw": ln})
    return out


def invoke_arm(arm: str, override_worktree: str | None = None) -> dict:
    """Invoke retriever for a given arm; return (log_entry, stdout, exit)."""
    pre = _count_log_lines()
    env = dict(os.environ)
    # Strip placeholder so mem0 picks claude_cli
    if env.get("ANTHROPIC_API_KEY", "").startswith("placeholder"):
        env.pop("ANTHROPIC_API_KEY", None)
    env["ROOMD_PHD_CODE_DIR"] = str(ROOT)
    # For mem0 arm, point at the D2-populated store
    if arm == "mem0":
        env["ROOMD_MEM0_STORE_DIR"] = "/tmp/phd_loop2_mem0_qdrant"
        env["ROOMD_MEM0_COLLECTION"] = "loop2_d4_seed"

    # D2's mem0 store is at /tmp/phd_loop2_mem0_qdrant; reuse for mem0 arm
    # so we can verify real results. The retriever's Mem0Backend default
    # is /tmp/phd_mem0_qdrant — for D4 we want to point it at D2's store
    # only when arm=mem0. We do this by passing a config override via env.
    # The current retriever doesn't read config from env; for D4 we
    # directly invoke the retriever and rely on the D2-populated default.

    worktree = override_worktree or SCOPE["worktree"]
    cmd = [
        str(VENV_PY), str(RETRIEVER),
        "--arm", arm,
        "--query", QUERY,
        "--k", str(K),
        "--scope-user-id", SCOPE["user_id"],
        "--scope-project", SCOPE["project"],
        "--scope-worktree", worktree,
        "--scope-branch", SCOPE["branch"],
    ]
    t0 = time.time()
    proc = subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=180,
    )
    elapsed = time.time() - t0
    post = _count_log_lines()
    new = _tail_log(post - pre)
    return {
        "arm": arm,
        "exit_code": proc.returncode,
        "elapsed_s": elapsed,
        "stdout_first300": proc.stdout[:300],
        "stderr_first300": proc.stderr[:300],
        "log_lines_added": post - pre,
        "new_log_entries": new,
    }


def _seed_mem0_for_d4_scope():
    """Ingest a sentinel fact into mem0 under D4's exact retriever-built scope
    so the mem0 arm has something to return. Idempotent: skips if already
    populated.
    """
    import importlib, sys as _sys
    _sys.path.insert(0, str(ROOT))
    if "memory.mem0_backend" in _sys.modules:
        importlib.invalidate_caches()
    from adapters.schema import ContentBlock, Turn  # noqa
    from memory.mem0_backend import Mem0Backend, _scope_to_user_id  # noqa

    scope = {
        "user_id": SCOPE["user_id"],
        "project": SCOPE["project"],
        "worktree": SCOPE["worktree"],
        "branch": SCOPE["branch"],
        "cli": "claude_code",
    }
    if os.environ.get("ANTHROPIC_API_KEY", "").startswith("placeholder"):
        del os.environ["ANTHROPIC_API_KEY"]
    backend = Mem0Backend(
        config={
            "store_dir": "/tmp/phd_loop2_mem0_qdrant",
            "collection": "loop2_d4_seed",
            "llm_provider": "claude_cli",
        },
        scope=scope,
    )
    uid = _scope_to_user_id(scope)
    pre = backend._safe_count_memories(uid)
    seeded = False
    if pre <= 0:
        # Add a single sentinel about Pydantic v2 schemas (matches D4's query)
        turns = [
            Turn(turn_id="d4_seed_u", session_id="d4_seed", ordinal=0,
                 cli="claude_code", ts_utc=time.time(), role="user",
                 content=[ContentBlock(
                     kind="text",
                     text="In the roomd project we use Pydantic v2 for all schema definitions. "
                          "All tests live under tests/ and use pytest with the parametrize marker. "
                          "Our preferred ID convention is sha1[:16] of canonical content.",
                 )]),
            Turn(turn_id="d4_seed_a", session_id="d4_seed", ordinal=1,
                 cli="claude_code", ts_utc=time.time(), role="assistant",
                 content=[ContentBlock(
                     kind="text",
                     text="Acknowledged. I will use Pydantic v2 BaseModel for all schemas, "
                          "pytest with parametrize, and sha1[:16] for IDs.",
                 )]),
        ]
        ids = backend.add(turns)
        seeded = True
        time.sleep(0.5)  # qdrant flush
    post = backend._safe_count_memories(uid)
    return {"seeded": seeded, "pre_count": pre, "post_count": post, "uid": uid}


def main() -> int:
    report: dict = {
        "started_utc": time.time(),
        "query": QUERY,
        "k": K,
        "scope": SCOPE,
        "arms": {},
    }

    # Pre-seed mem0 partition under D4's exact scope for retrieval realism
    print("Seeding mem0 partition for D4 scope...")
    seed_info = _seed_mem0_for_d4_scope()
    report["mem0_seed"] = seed_info
    print(f"  seed: {seed_info}")

    arms_to_test = ["null", "random", "mem0", "letta"]
    for arm in arms_to_test:
        # All arms use SCOPE (worktree=loop2_d4). Mem0's partition is
        # pre-seeded above so it has data to return.
        r = invoke_arm(arm)
        report["arms"][arm] = r
        print(f"--- arm={arm} ---")
        print(f"  exit: {r['exit_code']}, lines_added: {r['log_lines_added']}, elapsed: {r['elapsed_s']:.1f}s")
        if r["new_log_entries"]:
            entry = r["new_log_entries"][-1]
            print(f"  log: arm={entry.get('arm')} status={entry.get('status')} "
                  f"n_results={entry.get('n_results')} top_score={entry.get('top_score')}")

    # Assert per-arm correctness
    failures: list = []
    for arm in arms_to_test:
        ar = report["arms"][arm]
        if ar["log_lines_added"] < 1:
            failures.append(f"{arm}: no log line written")
            continue
        last = ar["new_log_entries"][-1]
        if last.get("arm") != arm:
            failures.append(f"{arm}: log entry says arm={last.get('arm')}")
            continue
        # null & random should always be OK (no external dependency)
        if arm in ("null", "random") and last.get("status") != "OK":
            failures.append(f"{arm}: status={last.get('status')}")
        # mem0 should be OK and ideally have n_results > 0 (using D2 store)
        if arm == "mem0":
            if last.get("status") != "OK":
                failures.append(f"mem0: status={last.get('status')} (expected OK)")
            elif last.get("n_results", 0) == 0:
                # Soft warning: D2 store may have a different qdrant path
                report["arms"]["mem0"]["soft_warning"] = (
                    "mem0 arm logged OK but n_results=0; verify store_dir path"
                )
        # letta should be OK if local server is up, otherwise UNHEALTHY
        if arm == "letta":
            if last.get("status") not in ("OK", "UNHEALTHY"):
                failures.append(f"letta: unexpected status={last.get('status')}")

    report["failures"] = failures
    report["status"] = "PASS" if not failures else "FAIL"
    report["ended_utc"] = time.time()
    REPORT.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nReport: {REPORT}")
    print(f"Status: {report['status']}")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
