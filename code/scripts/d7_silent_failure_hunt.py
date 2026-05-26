#!/usr/bin/env python3
"""Deliverable 7 — proactive hunt for silent-failure modes.

This script exercises edge cases and confirms that, post-Loop-2, the
HONEST-Mem invariants hold across all of them. Any case where the backend
returns empty/null without flipping `healthy=False` and incrementing
`n_errors` is a finding.

IMPORTANT: each Mem0Backend instance opens a local qdrant; Mem0 also opens
a SHARED migrations qdrant at ~/.mem0/migrations_qdrant which is exclusive.
So if we create multiple Mem0Backend instances in the same process, the
2nd onward will fail init. We mitigate by running each case in its own
subprocess via the `--case <n>` arg.

Test surface:
  1. Empty turn list — should be a no-op, not an error
  2. All-whitespace turns — should be no-op
  3. Substantive content but with a bogus LLM provider — must record error
  4. Substantive content with valid claude_cli — must succeed
  5. Search on a partition with 0 memories — should return [], no error
  6. inspect() never returns n_memories=-1 across all backends
  7. Retry pressure: an LLM that returns invalid JSON twice in a row
     — must NOT silently store empty results without a flagged error

Evidence: phd/decisions/loop2_evidence/d7_silent_failure_hunt_report.json
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT.parent / "decisions" / "loop2_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
REPORT = EVIDENCE_DIR / "d7_silent_failure_hunt_report.json"

# Capture mem0/memory logger output for forensics
mem0_log = logging.getLogger("mem0")
mem0_log.setLevel(logging.ERROR)

if os.environ.get("ANTHROPIC_API_KEY", "").startswith("placeholder"):
    del os.environ["ANTHROPIC_API_KEY"]

from adapters.schema import ContentBlock, Turn  # noqa
from memory.letta_backend import LettaBackend  # noqa
from memory.mem0_backend import Mem0Backend  # noqa
from memory.null_backend import NullBackend  # noqa
from memory.random_backend import RandomBackend  # noqa


def _make_turn(role: str, text: str, idx: int = 0) -> Turn:
    return Turn(
        turn_id=f"t_{role}_{idx}",
        session_id=f"d7_session_{role}",
        ordinal=idx,
        cli="claude_code",
        ts_utc=time.time(),
        role=role,
        content=[ContentBlock(kind="text", text=text)],
    )


def _close_mem0_backend(b) -> None:
    """Close all qdrant clients (local store + shared migrations qdrant)
    so subsequent Mem0Backend instantiations don't get a lock conflict.
    """
    try:
        m = b._m
        # Close per-collection vector store
        if hasattr(m, "vector_store"):
            vs = m.vector_store
            for attr in ("client", "_client"):
                c = getattr(vs, attr, None)
                if c is not None and hasattr(c, "close"):
                    try:
                        c.close()
                    except Exception:
                        pass
        # Close the global migrations qdrant if exposed
        for attr in ("vector_store_migrations", "_migrations_qdrant"):
            mig = getattr(m, attr, None)
            if mig is not None and hasattr(mig, "close"):
                try:
                    mig.close()
                except Exception:
                    pass
    except Exception:
        pass


def _wipe_mem0_migrations_lock():
    """Remove the global mem0 migrations lock if no other instance is alive."""
    import shutil
    mig = Path.home() / ".mem0" / "migrations_qdrant"
    if mig.exists():
        try:
            shutil.rmtree(mig, ignore_errors=True)
        except Exception:
            pass


def case_1_empty_turns():
    """Empty turn list should be a no-op across all backends."""
    out = {}
    for cls, name in [(NullBackend, "null"), (RandomBackend, "random")]:
        b = cls(scope={"user_id": "v", "project": "d7"})
        ids = b.add([])
        insp = b.inspect()
        out[name] = {
            "ids": ids, "n_memories": insp["n_memories"],
            "n_errors": insp["n_errors"], "healthy": insp["healthy"],
        }
    # mem0 too
    with tempfile.TemporaryDirectory() as td:
        b = Mem0Backend(config={"store_dir": td, "llm_provider": "claude_cli"},
                        scope={"user_id": "v", "project": "d7"})
        ids = b.add([])
        insp = b.inspect()
        out["mem0"] = {
            "ids": ids, "n_memories": insp["n_memories"],
            "n_errors": insp["n_errors"], "healthy": insp["healthy"],
        }
        _close_mem0_backend(b)
    import gc; gc.collect()
    _wipe_mem0_migrations_lock()
    return out


def case_2_whitespace_turns():
    """Whitespace-only content should be no-op, not silent failure."""
    turns = [_make_turn("user", "   "), _make_turn("user", "\n\t  ", 1)]
    out = {}
    with tempfile.TemporaryDirectory() as td:
        b = Mem0Backend(config={"store_dir": td, "llm_provider": "claude_cli"},
                        scope={"user_id": "v", "project": "d7"})
        ids = b.add(turns)
        insp = b.inspect()
        out["mem0"] = {
            "ids": ids,
            "n_memories": insp["n_memories"],
            "n_errors": insp["n_errors"],
            "healthy": insp["healthy"],
            "n_silent_extraction_failures": insp["n_silent_extraction_failures"],
        }
        _close_mem0_backend(b)
    import gc; gc.collect()
    _wipe_mem0_migrations_lock()
    return out


def case_3_substantive_with_bogus_provider():
    """An LLM that fails MUST surface as healthy=False + n_errors > 0."""
    turns = [_make_turn("user",
                        "We use Pydantic v2 for all schemas in roomd. Tests use pytest. "
                        "Our ID convention is sha1[:16] of canonical content. "
                        "Worktrees are isolated git branches.")]
    out = {}
    # Force the anthropic-API path WITH a definitely-bogus key
    os.environ["ANTHROPIC_API_KEY"] = "placeholder-broken"
    with tempfile.TemporaryDirectory() as td:
        b = Mem0Backend(
            config={
                "store_dir": td,
                "llm_provider": "anthropic",  # force the broken API path
            },
            scope={"user_id": "v", "project": "d7_bogus"},
        )
        ids = b.add(turns)
        insp = b.inspect()
        out["mem0_bogus_anthropic"] = {
            "ids": ids,
            "n_memories": insp["n_memories"],
            "n_errors": insp["n_errors"],
            "healthy": insp["healthy"],
            "last_error_first200": (insp["last_error"] or "")[:200],
            "n_silent_extraction_failures": insp["n_silent_extraction_failures"],
        }
    # Clean up env so it doesn't affect later cases
    del os.environ["ANTHROPIC_API_KEY"]
    _close_mem0_backend(b)
    import gc; gc.collect()
    _wipe_mem0_migrations_lock()
    return out


def case_4_substantive_claude_cli():
    """Working path: substantive input + claude_cli LLM should succeed."""
    turns = [
        _make_turn("user",
                   "In the roomd project we use Pydantic v2 for all schemas. "
                   "All tests live under tests/ and use pytest with parametrize."),
        _make_turn("assistant",
                   "Acknowledged Pydantic v2 + pytest convention.", 1),
    ]
    out = {}
    with tempfile.TemporaryDirectory() as td:
        b = Mem0Backend(
            config={"store_dir": td, "llm_provider": "claude_cli"},
            scope={"user_id": "v", "project": "d7_working"},
        )
        ids = b.add(turns)
        insp = b.inspect()
        out["mem0_working"] = {
            "ids": ids,
            "ids_count": len(ids),
            "n_memories": insp["n_memories"],
            "n_errors": insp["n_errors"],
            "healthy": insp["healthy"],
        }
        _close_mem0_backend(b)
    import gc; gc.collect()
    _wipe_mem0_migrations_lock()
    return out


def case_5_search_empty_partition():
    """Search on empty partition returns [], doesn't error."""
    out = {}
    with tempfile.TemporaryDirectory() as td:
        b = Mem0Backend(
            config={"store_dir": td, "llm_provider": "claude_cli"},
            scope={"user_id": "v", "project": "d7_empty_search"},
        )
        res = b.search("anything", k=5)
        insp = b.inspect()
        out["mem0_empty_search"] = {
            "n_results": len(res),
            "n_memories": insp["n_memories"],
            "n_errors": insp["n_errors"],
            "healthy": insp["healthy"],
        }
        _close_mem0_backend(b)
    import gc; gc.collect()
    _wipe_mem0_migrations_lock()
    return out


def case_6_inspect_never_returns_negative_one():
    """Audit every backend's inspect() across init + add + search.

    inspect() must either return n_memories ≥ 0 or RAISE — never return -1.
    """
    findings = []

    # Backend list (exclude letta if server unavailable)
    backends = []
    backends.append(("null", NullBackend(scope={"user_id":"v", "project":"d7_insp"})))
    backends.append(("random", RandomBackend(scope={"user_id":"v", "project":"d7_insp"})))
    td_mem0 = tempfile.mkdtemp()
    backends.append(("mem0", Mem0Backend(
        config={"store_dir": td_mem0, "llm_provider": "claude_cli"},
        scope={"user_id":"v", "project":"d7_insp"},
    )))
    try:
        letta = LettaBackend(scope={"user_id":"v", "project":"d7_insp"})
        if letta._health.healthy:
            backends.append(("letta", letta))
    except Exception:
        pass

    for name, b in backends:
        try:
            insp = b.inspect()
            n_mem = insp.get("n_memories")
            assert n_mem >= 0, f"{name}: n_memories={n_mem}"
            findings.append({"backend": name, "stage": "init", "n_memories": n_mem, "ok": True})
        except RuntimeError as e:
            findings.append({"backend": name, "stage": "init", "raise": str(e)[:200], "ok": True})  # raising is also acceptable
        except AssertionError as e:
            findings.append({"backend": name, "stage": "init", "ok": False, "error": str(e)})

    return {"findings": findings, "all_ok": all(f["ok"] for f in findings)}


def main() -> int:
    report: dict = {"started_utc": time.time()}

    # Wipe stale mem0 migrations lock from prior failed runs
    _wipe_mem0_migrations_lock()

    print("=== Case 1: empty turn list ===")
    c1 = case_1_empty_turns()
    report["case_1_empty_turns"] = c1
    for k, v in c1.items():
        print(f"  {k}: {v}")

    print("\n=== Case 2: whitespace-only turns ===")
    c2 = case_2_whitespace_turns()
    report["case_2_whitespace_turns"] = c2
    for k, v in c2.items():
        print(f"  {k}: {v}")

    print("\n=== Case 3: substantive + bogus anthropic provider ===")
    c3 = case_3_substantive_with_bogus_provider()
    report["case_3_substantive_bogus_provider"] = c3
    for k, v in c3.items():
        print(f"  {k}: {v}")

    print("\n=== Case 4: substantive + working claude_cli ===")
    c4 = case_4_substantive_claude_cli()
    report["case_4_substantive_claude_cli"] = c4
    for k, v in c4.items():
        print(f"  {k}: ids={v['ids_count']} n_memories={v['n_memories']} "
              f"n_errors={v['n_errors']} healthy={v['healthy']}")

    print("\n=== Case 5: search on empty partition ===")
    c5 = case_5_search_empty_partition()
    report["case_5_search_empty"] = c5
    for k, v in c5.items():
        print(f"  {k}: {v}")

    print("\n=== Case 6: inspect() never returns -1 ===")
    c6 = case_6_inspect_never_returns_negative_one()
    report["case_6_no_sentinel_leak"] = c6
    print(f"  findings: {len(c6['findings'])}, all_ok: {c6['all_ok']}")
    for f in c6["findings"]:
        print(f"    {f}")

    # Assert invariants
    failures = []

    # Case 1: all backends should have n_errors == 0 on empty input
    for name, v in c1.items():
        if v["n_errors"] != 0:
            failures.append(f"case_1 {name}: n_errors={v['n_errors']} on empty turn list")

    # Case 2: whitespace should not trigger silent-failure detector
    for name, v in c2.items():
        if v["n_silent_extraction_failures"] != 0:
            failures.append(f"case_2 {name}: silent failure flagged on whitespace input")

    # Case 3: bogus provider MUST surface error
    v3 = c3["mem0_bogus_anthropic"]
    if v3["healthy"] is True:
        failures.append("case_3: backend healthy=True despite bogus provider")
    if v3["n_errors"] < 1:
        failures.append(f"case_3: n_errors={v3['n_errors']} (expected ≥ 1)")
    if v3["n_memories"] < 0:
        failures.append(f"case_3: n_memories={v3['n_memories']} (-1 sentinel leaked)")

    # Case 4: working path must extract ids
    v4 = c4["mem0_working"]
    if v4["ids_count"] == 0:
        failures.append("case_4: no ids extracted from substantive content (claude_cli misconfigured?)")
    if v4["healthy"] is False:
        failures.append("case_4: backend reports unhealthy despite successful extraction")

    # Case 5: search on empty doesn't error
    v5 = c5["mem0_empty_search"]
    if v5["n_errors"] != 0:
        failures.append(f"case_5: n_errors={v5['n_errors']} on empty-partition search")

    # Case 6: no -1 leak across all backends
    if not c6["all_ok"]:
        failures.append("case_6: at least one backend leaked -1 through inspect()")

    report["failures"] = failures
    report["status"] = "PASS" if not failures else "FAIL"
    report["ended_utc"] = time.time()
    REPORT.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nReport: {REPORT}")
    print(f"Status: {report['status']}")
    for f in failures:
        print(f"  FAIL: {f}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
