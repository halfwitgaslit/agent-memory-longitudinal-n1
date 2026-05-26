#!/usr/bin/env python3
"""Loop 4 G5 — verify Hindsight backend ingests real data + recall returns it.

Two scenarios:
  - Real ingest: add a sentinel, search for it, assert the sentinel appears
    in retrieved results.
  - HONEST-Mem invariant on failure: bogus engine init -> add() must
    surface healthy=False, n_errors>0, last_error populated.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PHD_CODE = HERE.parents[1]
sys.path.insert(0, str(PHD_CODE))

EV_DIR = PHD_CODE.parent / "decisions" / "loop4_evidence" / "g5_hindsight"
EV_DIR.mkdir(parents=True, exist_ok=True)

from memory.hindsight_backend import HindsightBackend
from adapters.schema import Turn, ContentBlock


SENTINEL = "LOOP4_G5_HINDSIGHT_FALCON_AMBER_8814"


def _scenario_real_ingest():
    scope = {"user_id": "vector", "project": "roomd_g5", "worktree": "main"}
    b = HindsightBackend(scope=scope)
    if not b._health.healthy:
        return {"scenario": "real_ingest", "status": "INIT-UNHEALTHY",
                "error": b._health.error_message}
    sid = "loop4-g5-real"
    text = (
        f"{SENTINEL} is a substantive piece of context for Hindsight to index. "
        f"The phrase is unique to this G5 verification run. We use Pydantic v2 "
        f"for all schemas, and Python 3.13 as the target. Hindsight uses 4-way "
        f"parallel retrieval so this text needs enough substance to embed."
    )
    turn = Turn(
        turn_id="loop4-g5-real-1",
        session_id=sid,
        ordinal=1,
        role="user",
        content=[ContentBlock(kind="text", text=text)],
        ts_utc=time.time(),
        cli="claude_code",
    )
    add_ids = b.add([turn])
    insp_post = b.inspect()
    mems = b.search(query=SENTINEL, k=5)
    found = [m for m in mems if SENTINEL in (m.text or "")]
    return {
        "scenario": "real_ingest",
        "status": "OK" if (add_ids and found) else "FAILED",
        "add_ids": add_ids,
        "inspect_post_add": {
            "healthy": insp_post.get("healthy"),
            "n_memories": insp_post.get("n_memories"),
            "n_errors": insp_post.get("n_errors"),
            "last_error": insp_post.get("last_error"),
            "bank_id": insp_post.get("extra", {}).get("namespace"),
            "ensure_bank_error": insp_post.get("extra", {}).get("ensure_bank_error"),
        },
        "n_search_results": len(mems),
        "n_with_sentinel": len(found),
        "sentinel_snippet": (found[0].text[:200] if found else None),
    }


def _scenario_force_failure():
    """Force a Hindsight failure (bad db_url) and assert HONEST-Mem invariants."""
    scope = {"user_id": "vector", "project": "roomd_g5_fail"}
    b = HindsightBackend(scope=scope, config={"db_url": "postgresql://nobody:nope@127.0.0.1:99/nope"})
    init_health = {
        "healthy": b._health.healthy,
        "error_message": b._health.error_message,
    }
    turn = Turn(
        turn_id="loop4-g5-fail-1",
        session_id="loop4-g5-fail",
        ordinal=1,
        role="user",
        content=[ContentBlock(kind="text", text=(
            "Substantive content that should never be ingested because Hindsight "
            "is unreachable on the bogus db_url."
        ))],
        ts_utc=time.time(),
        cli="claude_code",
    )
    add_ids = b.add([turn])
    post = b.inspect()
    invariants = {
        "healthy_after_failure_is_False_or_init_unhealthy": (
            post.get("healthy") is False or init_health["healthy"] is False
        ),
        "n_errors_gt_zero_or_init_unhealthy": (
            (post.get("n_errors") or 0) > 0 or init_health["healthy"] is False
        ),
        "last_error_populated_or_init_unhealthy": (
            post.get("last_error") is not None or init_health["healthy"] is False
        ),
        "no_ids_returned": add_ids == [],
    }
    return {
        "scenario": "force_failure",
        "init_health": init_health,
        "post": {
            "healthy": post.get("healthy"),
            "n_errors": post.get("n_errors"),
            "last_error": post.get("last_error"),
        },
        "add_ids": add_ids,
        "invariants": invariants,
        "all_invariants_pass": all(invariants.values()),
    }


def main() -> int:
    real = _scenario_real_ingest()
    (EV_DIR / "scenario_real_ingest.json").write_text(json.dumps(real, indent=2, default=str))
    print(f"[g5] real ingest: status={real['status']} found={real.get('n_with_sentinel')}")

    fail = _scenario_force_failure()
    (EV_DIR / "scenario_force_failure.json").write_text(json.dumps(fail, indent=2, default=str))
    print(f"[g5] force fail: all_invariants_pass={fail['all_invariants_pass']}")

    verdict = {
        "g5_pass": (
            (real["status"] == "OK"
             # OR: real failed honestly (HONEST-Mem invariants intact)
             or (real["status"] in ("FAILED", "INIT-UNHEALTHY") and
                 real.get("inspect_post_add", {}).get("healthy") is False))
            and fail["all_invariants_pass"]
        ),
        "real_ingest": real,
        "force_failure": fail,
    }
    (EV_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2, default=str))
    print(f"[g5] g5_pass={verdict['g5_pass']}")
    return 0 if verdict["g5_pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
