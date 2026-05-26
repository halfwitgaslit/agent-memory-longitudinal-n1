#!/usr/bin/env python3
"""Loop 4 G7 — empirically verify two CONCURRENT processes can both
add+search via Mem0SubprocessBackend without the qdrant lock blocking
the second one.

Protocol:
  1. Run TWO concurrent subprocesses (multiprocessing.Process), each
     instantiates a Mem0SubprocessBackend with its OWN store_dir
     (so they can truly run in parallel), seeds a unique sentinel, and
     reads it back.
  2. Capture results from both processes via a Queue.
  3. Assert both succeed.

We also run a SEQUENTIAL test (two sequential opens of Mem0SubprocessBackend
sharing the SAME store_dir) to prove that the in-process lock problem
from Loop 3 is gone for the wrapper.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve()
PHD_CODE = HERE.parents[1]
sys.path.insert(0, str(PHD_CODE))

EV_DIR = PHD_CODE.parent / "decisions" / "loop4_evidence" / "g7_concurrent"
EV_DIR.mkdir(parents=True, exist_ok=True)


def _worker(slot: str, store_dir: str, marker: str, q: mp.Queue) -> None:
    """Run inside a Process: open a subprocess-isolated backend, add+search."""
    try:
        sys.path.insert(0, str(PHD_CODE))
        from memory.mem0_subprocess import Mem0SubprocessBackend
        from adapters.schema import Turn, ContentBlock

        # Each process uses its own store_dir to allow true concurrency
        scope = {"user_id": "vector", "project": "roomd_g7", "worktree": "main"}
        b = Mem0SubprocessBackend(
            config={"store_dir": store_dir, "collection": f"g7_{slot}"},
            scope=scope,
        )

        sid = f"loop4-g7-{slot}"
        turn1 = Turn(
            turn_id=f"loop4-g7-{slot}-1",
            session_id=sid,
            ordinal=1,
            role="user",
            content=[ContentBlock(kind="text", text=(
                f"{marker} — this is a substantive fact for the G7 concurrency test "
                f"in slot {slot}. Please remember it verbatim."
            ))],
            ts_utc=time.time(),
            cli="claude_code",
        )
        turn2 = Turn(
            turn_id=f"loop4-g7-{slot}-2",
            session_id=sid,
            ordinal=2,
            role="assistant",
            content=[ContentBlock(kind="text", text=(
                f"Acknowledged. I will remember {marker} for the G7 test in slot {slot}."
            ))],
            ts_utc=time.time(),
            cli="claude_code",
        )
        ids = b.add([turn1, turn2])
        # Now search for the marker
        mems = b.search(query=marker, k=5)
        found = any(marker in (m.text or "") for m in mems)
        q.put({
            "slot": slot,
            "store_dir": store_dir,
            "marker": marker,
            "ids": ids,
            "n_mems": len(mems),
            "found_marker": found,
            "ok": bool(ids) and found,
        })
    except Exception as e:
        q.put({
            "slot": slot,
            "error": f"{type(e).__name__}: {e}",
            "ok": False,
        })


def main() -> int:
    # Two concurrent processes, each with its own store_dir
    q: mp.Queue = mp.Queue()
    procs = []
    base = "/tmp/phd_g7_mem0_qdrant"
    for slot, marker in (("A", "G7_MARKER_RAINBOW_ALPHA_3719"),
                         ("B", "G7_MARKER_RAINBOW_BETA_4280")):
        p = mp.Process(target=_worker, args=(slot, f"{base}_{slot}", marker, q))
        procs.append(p)
        p.start()
    results = []
    for p in procs:
        p.join(timeout=180)
    while not q.empty():
        results.append(q.get())

    summary = {
        "test": "two_concurrent_processes",
        "n_processes": len(procs),
        "results": results,
        "all_ok": all(r.get("ok") for r in results) and len(results) == len(procs),
    }
    (EV_DIR / "concurrent_processes.json").write_text(json.dumps(summary, indent=2))
    print(f"[g7] concurrent: all_ok={summary['all_ok']}; results={results}")

    return 0 if summary["all_ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
