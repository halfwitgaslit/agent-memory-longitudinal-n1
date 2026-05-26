"""Eval runner: scan sessions, compute metrics, append idempotently to JSONL.

Reuses the HMA-1 idempotent-JSONL pattern from
`distillation/code/hma_audit_mini/harness_runner.py`. The Phase-2 longitudinal
deployment will call this periodically as Vector accumulates real sessions
under different arms.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional

from adapters.claude_code_jsonl import (
    iter_roomd_sessions,
    parse_claude_code_session,
)
from adapters.codex_rollout_jsonl import iter_codex_sessions, parse_codex_rollout
from .metrics import MetricSet, compute_session_metrics, load_task_record


# ---------------------------------------------------------------------------
# Output store: append-only JSONL with per-session deduplication


DEFAULT_RESULTS_DIR = Path("/Users/aiSandbox/github/claude_can_do_anything/distillation/phd/results")


def _existing_session_ids(jsonl_path: Path) -> set:
    if not jsonl_path.exists():
        return set()
    seen = set()
    with jsonl_path.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if d.get("session_id"):
                    seen.add(d["session_id"])
            except Exception:
                continue
    return seen


def _append_metric(jsonl_path: Path, metric: MetricSet) -> None:
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a") as f:
        f.write(json.dumps(asdict(metric), sort_keys=True, default=str) + "\n")


# ---------------------------------------------------------------------------
# Arm assignment lookup
# Vector records {session_id → arm} via the skill at injection time
# (~/.roomd/mem_inject_log.jsonl). We map session → arm by joining on session_id.


def load_arm_assignments(log_path: str | Path = "~/.roomd/mem_inject_log.jsonl") -> dict:
    """Read the skill's injection log to derive {session_id → arm}."""
    p = Path(log_path).expanduser()
    if not p.exists():
        return {}
    assignments = {}
    with p.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                sid = d.get("scope", {}).get("session_id") or d.get("session_id")
                arm = d.get("arm")
                if sid and arm:
                    assignments[sid] = arm
            except Exception:
                continue
    return assignments


# ---------------------------------------------------------------------------
# Runner


def run_eval(
    output_path: str | Path = DEFAULT_RESULTS_DIR / "session_metrics.jsonl",
    task_records_dir: str | Path = "~/.roomd/task_records",
    arm_log: str | Path = "~/.roomd/mem_inject_log.jsonl",
    include_claude_code: bool = True,
    include_codex: bool = True,
    cwd_filter: str = "roomd",
    max_sessions: Optional[int] = None,
) -> dict:
    """Scan sessions; compute metrics; append new rows to the output JSONL."""
    output_path = Path(output_path)
    task_records_dir = Path(task_records_dir).expanduser()
    seen = _existing_session_ids(output_path)
    arms = load_arm_assignments(arm_log)

    n_processed = 0
    n_skipped = 0
    n_errors = 0
    sources_iter: List[tuple] = []

    if include_claude_code:
        sources_iter.append(("claude_code", list(iter_roomd_sessions())))
    if include_codex:
        sources_iter.append(
            ("codex", list(iter_codex_sessions(require_cwd_contains=cwd_filter)))
        )

    for cli_label, paths in sources_iter:
        for jsonl in paths:
            if max_sessions is not None and n_processed >= max_sessions:
                break
            try:
                if cli_label == "claude_code":
                    session = parse_claude_code_session(jsonl)
                else:
                    session = parse_codex_rollout(jsonl)
            except Exception as e:
                n_errors += 1
                print(f"[runner] parse error {jsonl.name}: {type(e).__name__}: {e}")
                continue
            if session.session_id in seen:
                n_skipped += 1
                continue
            arm = arms.get(session.session_id, "unknown")
            task_record = load_task_record(session.session_id, task_records_dir)
            try:
                metric = compute_session_metrics(session, arm=arm, task_record=task_record)
            except Exception as e:
                n_errors += 1
                print(f"[runner] metric error {session.session_id}: {type(e).__name__}: {e}")
                continue
            _append_metric(output_path, metric)
            seen.add(session.session_id)
            n_processed += 1
            if n_processed % 25 == 0:
                print(f"[runner] processed {n_processed} new sessions")

    return {
        "output_path": str(output_path),
        "n_processed": n_processed,
        "n_skipped": n_skipped,
        "n_errors": n_errors,
        "ts_utc": time.time(),
    }


# ---------------------------------------------------------------------------
# CLI


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default=str(DEFAULT_RESULTS_DIR / "session_metrics.jsonl"))
    ap.add_argument("--task-records-dir", default="~/.roomd/task_records")
    ap.add_argument("--arm-log", default="~/.roomd/mem_inject_log.jsonl")
    ap.add_argument("--no-claude-code", action="store_true")
    ap.add_argument("--no-codex", action="store_true")
    ap.add_argument("--cwd-filter", default="roomd")
    ap.add_argument("--max-sessions", type=int, default=None)
    args = ap.parse_args()

    summary = run_eval(
        output_path=args.output,
        task_records_dir=args.task_records_dir,
        arm_log=args.arm_log,
        include_claude_code=not args.no_claude_code,
        include_codex=not args.no_codex,
        cwd_filter=args.cwd_filter,
        max_sessions=args.max_sessions,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
