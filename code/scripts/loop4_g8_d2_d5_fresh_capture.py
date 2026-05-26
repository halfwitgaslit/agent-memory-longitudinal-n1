#!/usr/bin/env python3
"""Loop 4 G8 — Rerun D2 and D5 with FRESH stores and capture real extraction
evidence.

Loop 3 found that D2 / D5 evidence files contained `skipped_idempotent: true`
and `cli_meter.total_calls: 0`, meaning the stores were already populated
from prior unrecorded runs. The "10 turns -> 4 facts" and "5 Codex turns -> 4
facts" claims had no captured evidence in the official record.

This script:
  1. Wipes the D2 store dir (`/tmp/phd_loop2_mem0_qdrant`) BEFORE running.
  2. Wipes the D5 store dir (`/tmp/phd_loop2_mem0_qdrant_d5`) BEFORE running.
  3. Re-runs both with fresh stores.
  4. Captures all evidence to phd/decisions/loop4_evidence/g8_d2_d5_fresh/.

We use the existing d2_mem0_e2e.py and d5_cross_cli_bridging.py — the
idempotency check now sees empty stores and DOES the real ingest, so
cli_meter > 0 and new_ids > 0.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PHD_CODE = HERE.parents[1]
EV_DIR = PHD_CODE.parent / "decisions" / "loop4_evidence" / "g8_d2_d5_fresh"
EV_DIR.mkdir(parents=True, exist_ok=True)

D2_STORE = Path("/tmp/phd_loop2_mem0_qdrant")
# G8 fix: D5 uses /tmp/phd_loop2_d5_mem0_qdrant (NOT /tmp/phd_loop2_mem0_qdrant_d5).
# The previous run with the wrong path left D5's actual store untouched,
# triggering the same idempotent-skip the Loop 3 audit caught.
D5_STORE = Path("/tmp/phd_loop2_d5_mem0_qdrant")
GLOBAL_LOCK = Path.home() / ".mem0" / "migrations_qdrant" / ".lock"
SUBPROC_LOCK = Path.home() / ".mem0" / ".phd_mem0_subprocess_lock"


def _wipe(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _record_state(label: str) -> dict:
    """Snapshot disk state of the qdrant dirs."""
    return {
        "label": label,
        "d2_store_exists": D2_STORE.exists(),
        "d5_store_exists": D5_STORE.exists(),
        "global_lock_exists": GLOBAL_LOCK.exists(),
        "subproc_lock_exists": SUBPROC_LOCK.exists(),
    }


def _run_script(script: Path) -> dict:
    py = PHD_CODE / ".venv" / "bin" / "python"
    t0 = time.time()
    proc = subprocess.run(
        [str(py), str(script)],
        cwd=str(PHD_CODE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=600,
    )
    duration = time.time() - t0
    return {
        "script": str(script),
        "rc": proc.returncode,
        "stdout": proc.stdout.decode("utf-8", errors="replace"),
        "stderr": proc.stderr.decode("utf-8", errors="replace"),
        "duration_s": round(duration, 2),
    }


def _read_evidence(rel_path: str) -> dict | None:
    p = PHD_CODE.parent / rel_path
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"raw": p.read_text()[:2000]}


def main() -> int:
    # Pre-flight
    pre = _record_state("pre-wipe")
    print(f"[g8] pre-wipe state: {pre}")
    # Wipe stores (and the locks for hygiene)
    _wipe(D2_STORE)
    _wipe(D5_STORE)
    try:
        if GLOBAL_LOCK.exists():
            GLOBAL_LOCK.unlink()
    except Exception:
        pass
    try:
        if SUBPROC_LOCK.exists():
            SUBPROC_LOCK.unlink()
    except Exception:
        pass
    post_wipe = _record_state("post-wipe")
    print(f"[g8] post-wipe state: {post_wipe}")

    # Run D2 fresh
    print(f"[g8] running D2 with fresh store...")
    d2_run = _run_script(PHD_CODE / "scripts" / "d2_mem0_e2e.py")
    print(f"[g8] D2 rc={d2_run['rc']} duration={d2_run['duration_s']}s")
    (EV_DIR / "d2_run.json").write_text(json.dumps(d2_run, indent=2, default=str))

    # The D2 script writes to phd/decisions/loop2_evidence/d2_mem0_e2e_report.json
    # We read it and copy a fresh-captured version into loop4_evidence.
    d2_report = _read_evidence("decisions/loop2_evidence/d2_mem0_e2e_report.json")
    if d2_report:
        (EV_DIR / "d2_mem0_e2e_report_fresh.json").write_text(
            json.dumps(d2_report, indent=2, default=str)
        )

    # Run D5 fresh
    print(f"[g8] running D5 with fresh store...")
    d5_run = _run_script(PHD_CODE / "scripts" / "d5_cross_cli_bridging.py")
    print(f"[g8] D5 rc={d5_run['rc']} duration={d5_run['duration_s']}s")
    (EV_DIR / "d5_run.json").write_text(json.dumps(d5_run, indent=2, default=str))

    d5_report = _read_evidence("decisions/loop2_evidence/d5_cross_cli_bridging_report.json")
    if d5_report:
        (EV_DIR / "d5_cross_cli_bridging_report_fresh.json").write_text(
            json.dumps(d5_report, indent=2, default=str)
        )

    # Verdict
    verdict: dict = {
        "d2_rc": d2_run["rc"],
        "d5_rc": d5_run["rc"],
    }

    # Analyze D2 evidence for the "fresh capture" criteria
    if d2_report and isinstance(d2_report.get("stages"), list):
        ingest_stage = next(
            (s for s in d2_report["stages"] if s.get("name") == "ingest_real"),
            {},
        )
        verdict["d2_ingest"] = {
            "skipped_idempotent": ingest_stage.get("skipped_idempotent"),
            "n_ids_returned": ingest_stage.get("n_ids_returned"),
            "post_n_memories": ingest_stage.get("post_n_memories"),
            "cli_meter_total_calls": (ingest_stage.get("cli_meter") or {}).get("total_calls"),
            "fresh_capture_criteria_met": (
                ingest_stage.get("skipped_idempotent") is False
                and (ingest_stage.get("n_ids_returned") or 0) > 0
                and ((ingest_stage.get("cli_meter") or {}).get("total_calls") or 0) > 0
            ),
        }
    if d5_report:
        # D5 layout: top-level "ingest" + "final_cli_meter"
        ingest_summary = d5_report.get("ingest") or {}
        cli_meter_final = d5_report.get("final_cli_meter") or {}
        verdict["d5_ingest"] = {
            "skipped_idempotent": ingest_summary.get("skipped_idempotent"),
            "new_ids_count": ingest_summary.get("new_ids_count"),
            "pre_count": ingest_summary.get("pre_count"),
            "post_count": ingest_summary.get("post_count"),
            "final_cli_meter_total_calls": cli_meter_final.get("total_calls"),
            "final_cli_meter_total_usd": cli_meter_final.get("total_usd"),
            "fresh_capture_criteria_met": (
                ingest_summary.get("skipped_idempotent") is False
                and (ingest_summary.get("new_ids_count") or 0) > 0
                and (cli_meter_final.get("total_calls") or 0) > 0
            ),
        }
    verdict["g8_pass"] = (
        d2_run["rc"] == 0 and d5_run["rc"] == 0
        and verdict.get("d2_ingest", {}).get("fresh_capture_criteria_met") is True
        and verdict.get("d5_ingest", {}).get("fresh_capture_criteria_met") is True
    )
    (EV_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2, default=str))
    print(f"[g8] verdict: {json.dumps(verdict, default=str)[:400]}")
    print(f"[g8] g8_pass={verdict['g8_pass']}")
    return 0 if verdict["g8_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
