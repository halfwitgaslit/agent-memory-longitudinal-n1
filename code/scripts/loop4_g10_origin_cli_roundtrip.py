#!/usr/bin/env python3
"""Loop 4 G10 — Empirically verify _origin_cli round-trips through bridge mode.

Setup:
  - Write a "claude_code" turn with marker MARKER_CC into bridge_scope (cli omitted)
  - Write a "codex" turn with marker MARKER_CX into bridge_scope (cli omitted)
  - Search bridge_scope for both markers
  - Assert: results carry metadata["_origin_cli"] set to the correct CLI

This proves the eval harness can distinguish Codex-originated from
Claude-Code-originated memories even when they share a scope partition.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PHD_CODE = HERE.parents[1]
sys.path.insert(0, str(PHD_CODE))

EV_DIR = PHD_CODE.parent / "decisions" / "loop4_evidence" / "g10_origin_cli"
EV_DIR.mkdir(parents=True, exist_ok=True)

from memory.mem0_backend import Mem0Backend
from adapters.schema import Turn, ContentBlock

MARKER_CC = "LOOP4_G10_CC_PORCUPINE_5471"
MARKER_CX = "LOOP4_G10_CX_ZEPPELIN_9938"


def _clear_lock():
    p = Path.home() / ".mem0" / "migrations_qdrant" / ".lock"
    if p.exists():
        try:
            p.unlink()
        except Exception:
            pass


def _seed(cli_value: str, marker: str, scope: dict) -> dict:
    """Add a turn into bridge_scope tagged with the given originating CLI."""
    _clear_lock()
    b = Mem0Backend(
        config={"store_dir": "/tmp/phd_g10_mem0_qdrant", "collection": "loop4_g10"},
        scope=scope,
    )
    if not b._health.healthy:
        return {"ok": False, "error": b._health.error_message}
    sid = f"loop4-g10-{cli_value}"
    turn = Turn(
        turn_id=f"loop4-g10-{cli_value}-1",
        session_id=sid,
        ordinal=1,
        role="user",
        content=[ContentBlock(kind="text", text=(
            f"{marker} — this is a substantive piece of context originating from "
            f"the {cli_value} CLI. Please remember it for future cross-CLI bridging tests."
        ))],
        ts_utc=time.time(),
        cli=cli_value,  # type: ignore
    )
    turn2 = Turn(
        turn_id=f"loop4-g10-{cli_value}-2",
        session_id=sid,
        ordinal=2,
        role="assistant",
        content=[ContentBlock(kind="text", text=(
            f"Acknowledged. I will remember {marker} as a {cli_value}-originated fact."
        ))],
        ts_utc=time.time(),
        cli=cli_value,  # type: ignore
    )
    ids = b.add([turn, turn2])
    insp = b.inspect()
    return {"ok": True, "ids": ids, "n_after": insp.get("n_memories"), "healthy": insp.get("healthy")}


def main() -> int:
    bridge_scope = {
        "user_id": "vector",
        "project": "roomd",
        "worktree": "main",
        "branch": "main",
        # cli intentionally OMITTED — this is bridge mode
    }

    print(f"[g10] seeding claude_code marker {MARKER_CC} into bridge_scope")
    r1 = _seed("claude_code", MARKER_CC, bridge_scope)
    print(f"[g10] seed CC: {r1}")
    (EV_DIR / "seed_cc.json").write_text(json.dumps(r1, indent=2, default=str))

    print(f"[g10] seeding codex marker {MARKER_CX} into bridge_scope")
    r2 = _seed("codex", MARKER_CX, bridge_scope)
    print(f"[g10] seed CX: {r2}")
    (EV_DIR / "seed_cx.json").write_text(json.dumps(r2, indent=2, default=str))

    if not (r1.get("ok") and r2.get("ok")):
        print(f"[g10] cannot proceed — seeding failed")
        return 1

    # Now search bridge_scope for both markers and verify metadata
    _clear_lock()
    b = Mem0Backend(
        config={"store_dir": "/tmp/phd_g10_mem0_qdrant", "collection": "loop4_g10"},
        scope=bridge_scope,
    )

    summary = {"markers_found": {}, "origin_cli_observed": {}, "verdict": None}

    for label, marker, expected_cli in (
        ("cc", MARKER_CC, "claude_code"),
        ("cx", MARKER_CX, "codex"),
    ):
        mems = b.search(query=marker, k=5)
        found = []
        for m in mems:
            if marker in (m.text or ""):
                found.append({
                    "memory_id": m.memory_id,
                    "text": (m.text or "")[:200],
                    "origin_cli": (m.metadata or {}).get("_origin_cli"),
                    "origin_scope_user_id": (m.metadata or {}).get("_origin_scope_user_id"),
                    "score": m.score,
                })
        summary["markers_found"][label] = {
            "marker": marker,
            "expected_origin_cli": expected_cli,
            "n_results": len(mems),
            "n_with_marker": len(found),
            "found": found,
        }
        # Aggregate the observed _origin_cli values
        if found:
            summary["origin_cli_observed"][label] = found[0]["origin_cli"]
        else:
            summary["origin_cli_observed"][label] = None

    cc_ok = summary["origin_cli_observed"].get("cc") == "claude_code"
    cx_ok = summary["origin_cli_observed"].get("cx") == "codex"

    summary["verdict"] = {
        "cc_origin_cli_correct": cc_ok,
        "cx_origin_cli_correct": cx_ok,
        "g10_pass": cc_ok and cx_ok,
    }
    (EV_DIR / "search_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"[g10] verdict: {json.dumps(summary['verdict'])}")
    return 0 if summary["verdict"]["g10_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
