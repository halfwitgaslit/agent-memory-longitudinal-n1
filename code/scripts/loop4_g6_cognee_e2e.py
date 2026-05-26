#!/usr/bin/env python3
"""Loop 4 G6 — verify Cognee backend EITHER works with a real API key OR
fails honestly (HONEST-Mem invariants hold).

The pre-reg locks Cognee with Anthropic Haiku graph extraction. In our
offline test env we have no ANTHROPIC_API_KEY. Two valid outcomes:
  - With real key: full e2e success (sentinel ingest + retrieve)
  - Without real key: add() fails, healthy=False, n_errors>0, last_error
    populated. No synthetic IDs.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PHD_CODE = HERE.parents[1]
sys.path.insert(0, str(PHD_CODE))

EV_DIR = PHD_CODE.parent / "decisions" / "loop4_evidence" / "g6_cognee"
EV_DIR.mkdir(parents=True, exist_ok=True)

from memory.cognee_backend import CogneeBackend
from adapters.schema import Turn, ContentBlock

SENTINEL = "LOOP4_G6_COGNEE_OTTER_VIOLET_3201"


def _scenario_default():
    """Try ingest with default config (no override). Inspect what happens."""
    api_key_present = bool(os.environ.get("ANTHROPIC_API_KEY"))
    api_key_real = api_key_present and not (
        os.environ["ANTHROPIC_API_KEY"].lower().startswith("placeholder")
    )
    scope = {"user_id": "vector", "project": "roomd_g6", "worktree": "main"}
    b = CogneeBackend(scope=scope)
    if not b._health.healthy:
        return {
            "scenario": "default",
            "api_key_real": api_key_real,
            "status": "INIT-UNHEALTHY",
            "error_message": b._health.error_message,
        }
    sid = "loop4-g6"
    text = (
        f"{SENTINEL} is a substantive content sample for Cognee to ingest and "
        f"index. We use Python 3.13 and Pydantic v2 across the roomd project. "
        f"This phrase is unique to the G6 verification."
    )
    turn = Turn(
        turn_id="loop4-g6-1",
        session_id=sid,
        ordinal=1,
        role="user",
        content=[ContentBlock(kind="text", text=text)],
        ts_utc=time.time(),
        cli="claude_code",
    )
    add_ids = b.add([turn])
    insp = b.inspect()
    mems = b.search(query=SENTINEL, k=5) if (insp.get("healthy") and add_ids) else []
    found = [m for m in mems if SENTINEL in (m.text or "")]
    return {
        "scenario": "default",
        "api_key_real": api_key_real,
        "status": "OK" if (add_ids and found) else (
            "INGESTED-NO-RETRIEVE" if add_ids else "INGEST-FAILED"
        ),
        "add_ids": add_ids,
        "inspect_post_add": {
            "healthy": insp.get("healthy"),
            "n_memories": insp.get("n_memories"),
            "n_errors": insp.get("n_errors"),
            "last_error": insp.get("last_error"),
            "last_cognify_error": insp.get("extra", {}).get("last_cognify_error"),
        },
        "n_search_results": len(mems),
        "n_with_sentinel": len(found),
        "sentinel_snippet": (found[0].text[:200] if found else None),
    }


def _check_honest_invariants(default_result: dict) -> dict:
    """Cognee G6 invariants:

    If status==OK -> sentinel retrieved end-to-end, no further checks.
    Else -> we must see healthy=False AND (n_errors > 0 OR last_error
    populated OR last_cognify_error populated). The Loop-3 bug was
    silently returning synthetic IDs without indexing anything.
    """
    if default_result["status"] == "OK":
        return {"verdict": "REAL-SUCCESS", "all_pass": True}
    insp = default_result.get("inspect_post_add") or {}
    invariants = {
        "healthy_after_failure_is_False": insp.get("healthy") is False,
        "some_error_surfaced": (
            (insp.get("n_errors") or 0) > 0
            or insp.get("last_error") is not None
            or insp.get("last_cognify_error") is not None
        ),
        # If we got IDs without actually retrieving, that's STILL acceptable
        # provided the backend also marks unhealthy or surfaces last_cognify_error
        # (e.g., LLM extract failed). The bug we're guarding against is
        # IDs returned + healthy=True + no errors anywhere.
        "no_silent_success": not (
            default_result.get("add_ids")
            and insp.get("healthy") is True
            and (insp.get("n_errors") or 0) == 0
            and insp.get("last_cognify_error") is None
            and default_result["n_with_sentinel"] == 0
        ),
    }
    return {
        "verdict": "HONEST-FAILURE" if all(invariants.values()) else "BROKEN-HONEST-MEM",
        "invariants": invariants,
        "all_pass": all(invariants.values()),
    }


def main() -> int:
    default = _scenario_default()
    (EV_DIR / "scenario_default.json").write_text(json.dumps(default, indent=2, default=str))
    print(f"[g6] default: status={default['status']} api_key_real={default.get('api_key_real')}")

    inv = _check_honest_invariants(default)
    (EV_DIR / "honest_mem_check.json").write_text(json.dumps(inv, indent=2))
    print(f"[g6] honest_mem: verdict={inv['verdict']} all_pass={inv['all_pass']}")

    verdict = {
        "g6_pass": inv["all_pass"],
        "default_status": default["status"],
        "honest_mem_verdict": inv["verdict"],
        "invariants": inv.get("invariants"),
        "operational_note": (
            "When ANTHROPIC_API_KEY is absent, Cognee's LLM-extraction path "
            "fails. Phase 2 must either set a real API key or accept Cognee "
            "as a SKIPPED-UNHEALTHY arm (degradation strategy from "
            "architecture/v1.md §4.2)."
        ),
    }
    (EV_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(f"[g6] g6_pass={verdict['g6_pass']}")
    return 0 if verdict["g6_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
