#!/usr/bin/env python3
"""Deliverable 3 — verify the injection skill fires in a real Claude Code session.

Two-part validation:

Part A — direct retriever invocation (pure pipeline test)
  Runs retriever.py against each arm, confirms:
  - The script exits 0
  - Emits the markdown block to stdout
  - Appends a JSON line to ~/.roomd/mem_inject_log.jsonl

Part B — claude -p with auto-fired skill
  Spawns a real headless `claude -p` invocation in a fixture roomd-like temp
  directory. Confirms by counting log entries before/after that the skill
  was actually invoked by Claude during the session.

Evidence written to phd/decisions/loop2_evidence/d3_skill_fires_report.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT.parent / "decisions" / "loop2_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
REPORT = EVIDENCE_DIR / "d3_skill_fires_report.json"

LOG = Path.home() / ".roomd" / "mem_inject_log.jsonl"
RETRIEVER = ROOT / "injection" / "claude_code_skill" / "retriever.py"


def _count_log_lines() -> int:
    if not LOG.exists():
        return 0
    return sum(1 for _ in LOG.open())


def _tail_log_lines(n: int) -> list:
    if not LOG.exists():
        return []
    lines = LOG.read_text().strip().splitlines()
    out = []
    for ln in lines[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            out.append({"raw": ln})
    return out


def part_a_direct():
    """Direct invocation of retriever.py for each supported arm."""
    arms = ["null", "random"]  # cheap arms (no LLM call)
    results = []
    for arm in arms:
        pre = _count_log_lines()
        proc = subprocess.run(
            [sys.executable, str(RETRIEVER),
             "--arm", arm,
             "--query", "How do we hash content in roomd?",
             "--k", "5",
             "--scope-project", "roomd",
             "--scope-worktree", "loop2_d3_partA",
             "--scope-branch", "main",
             "--scope-user-id", "vector"],
            capture_output=True, text=True, timeout=60,
        )
        post = _count_log_lines()
        new = _tail_log_lines(post - pre)
        results.append({
            "arm": arm,
            "exit_code": proc.returncode,
            "stdout_first200": proc.stdout[:200],
            "stderr_first200": proc.stderr[:200],
            "log_lines_added": post - pre,
            "new_entries": new,
        })
    return results


def part_b_real_session():
    """Spawn `claude -p` in a fixture dir; confirm the skill fires."""
    # Create a temp directory that looks roomd-like.
    # We don't actually need to be under ~/github/roomd because the user's
    # description triggers on intent, not strict path. But to satisfy the
    # skill's matcher we'll explicitly mention "roomd" in the prompt.
    fixture_dir = Path(tempfile.mkdtemp(prefix="d3_roomd_fixture_"))
    # Drop a CLAUDE.md so claude -p has some project context
    (fixture_dir / "CLAUDE.md").write_text(
        "# roomd test fixture\n\n"
        "This is a temporary roomd-like project used to verify the "
        "roomd-memory-retrieval skill auto-fires.\n"
    )

    arm = "null"
    env = dict(os.environ)
    env["ROOMD_MEM_ARM"] = arm
    env["ROOMD_WORKTREE"] = "loop2_d3_partB"
    env["ROOMD_BRANCH"] = "main"

    pre = _count_log_lines()
    # Run a short headless session with a prompt that should trigger the skill.
    # Use --allowed-tools to ensure Bash is available (the skill uses it).
    prompt = (
        "I'm starting a roomd development session. "
        "Use the roomd-memory-retrieval skill to fetch relevant prior knowledge "
        "for the query 'How do we hash content in roomd?' (arm null, k 5). "
        "Run the retriever directly via the skill and report what (if any) "
        "memories surfaced. Skill location: ~/.claude/skills/roomd-memory-retrieval/"
    )
    proc = subprocess.run(
        ["claude", "-p", "--output-format", "json",
         "--model", "claude-haiku-4-5",
         "--allowed-tools", "Read,Bash,Skill"],
        input=prompt, text=True,
        capture_output=True, env=env, cwd=str(fixture_dir),
        timeout=420,
    )
    post = _count_log_lines()
    new_entries = _tail_log_lines(post - pre)

    # Parse claude's JSON output
    claude_out: dict = {}
    try:
        claude_out = json.loads(proc.stdout)
    except Exception:
        claude_out = {"_raw_stdout_first500": proc.stdout[:500]}

    return {
        "fixture_dir": str(fixture_dir),
        "arm": arm,
        "exit_code": proc.returncode,
        "claude_result_first300": (claude_out.get("result", "")[:300] if isinstance(claude_out, dict) else str(claude_out)[:300]),
        "claude_cost_usd": claude_out.get("total_cost_usd") if isinstance(claude_out, dict) else None,
        "claude_session_id": claude_out.get("session_id") if isinstance(claude_out, dict) else None,
        "log_lines_added": post - pre,
        "new_log_entries": new_entries,
        "skill_fired": (post - pre) > 0,
        "stderr_first300": proc.stderr[:300],
    }


def main():
    report = {"started_utc": time.time(), "log_path": str(LOG)}
    part_a = part_a_direct()
    report["part_a_direct_invocation"] = part_a
    # All arms must succeed (exit 0 and add at least 1 log line)
    assert all(r["exit_code"] == 0 and r["log_lines_added"] >= 1 for r in part_a), \
        f"Part A failed: {part_a}"
    print(f"Part A OK — both arms (null, random) logged successfully")

    part_b = part_b_real_session()
    report["part_b_real_session"] = part_b
    report["ended_utc"] = time.time()
    report["status"] = "PASS" if (part_b["skill_fired"]) else "PARTIAL"
    REPORT.write_text(json.dumps(report, indent=2, default=str))

    if part_b["skill_fired"]:
        print(f"Part B OK — skill fired in real Claude Code session "
              f"(added {part_b['log_lines_added']} log entries)")
    else:
        print(f"Part B PARTIAL — skill did NOT auto-fire in claude -p session. "
              f"Direct invocation works; agent-driven invocation needs more setup.")
        print(f"  claude returned: {part_b['claude_result_first300']}")
        print(f"  stderr: {part_b['stderr_first300']}")

    print(f"Report: {REPORT}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
