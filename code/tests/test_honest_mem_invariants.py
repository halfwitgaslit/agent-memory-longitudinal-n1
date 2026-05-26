"""HONEST-Mem invariant tests (Loop 2 fix).

These tests enforce the post-Loop-2 reporting contract:

1. `inspect()['n_memories']` MUST be a real non-negative count, never -1.
   If the count cannot be determined, `inspect()` MUST raise.
2. When an `add()` extracts ZERO facts on substantive input, `n_errors`
   MUST increment AND `healthy` MUST flip to False.
3. `last_error` MUST be populated whenever `n_errors > 0`.
4. `n_silent_extraction_failures` is a new field that distinguishes
   "the substrate quietly returned nothing" from "the call raised".

These are the failure modes HONEST-Mem (architecture/v1.md §4.5) is meant
to detect. Catching them in our own code is the precondition for being
allowed to report on other people's substrates.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.schema import ContentBlock, Turn  # noqa: E402
from memory.base import BackendHealth, MemoryBackend  # noqa: E402
from memory.mem0_backend import Mem0Backend  # noqa: E402
from memory.null_backend import NullBackend  # noqa: E402


def _make_substantive_turns():
    """A list of substantive Turns (>>100 chars total) suitable for testing
    that an add() should yield at least one fact under normal operation.
    """
    turns = []
    msgs = [
        ("user", "We use Pydantic v2 for all schema definitions in the roomd project. "
                 "All tests live under tests/ and we use pytest with parametrize. "
                 "Our preferred ID convention is sha1[:16] of the canonical content."),
        ("assistant", "Acknowledged. I will use Pydantic v2 BaseModel for all schemas, "
                     "follow the pytest parametrize pattern, and use sha1-truncated IDs."),
    ]
    for i, (role, text) in enumerate(msgs):
        turns.append(Turn(
            turn_id=f"t_{role}_{i}",
            session_id="honest_mem_session",
            ordinal=i,
            cli="claude_code",
            ts_utc=0.0,
            role=role,
            content=[ContentBlock(kind="text", text=text)],
        ))
    return turns


def test_inspect_never_returns_negative_n_memories_for_null_backend():
    """NullBackend should always report n_memories=0 in inspect()."""
    b = NullBackend(scope={"user_id": "test", "project": "honest_mem"})
    insp = b.inspect()
    assert insp["n_memories"] == 0
    assert insp["healthy"] is True
    assert "last_error" in insp
    assert insp["last_error"] is None
    assert insp["n_silent_extraction_failures"] == 0


def test_inspect_raises_on_negative_sentinel():
    """If a backend somehow ends up with n_memories=-1, inspect() raises."""
    b = NullBackend()
    # Forcibly set the bad sentinel
    b._health.n_memories = -1
    with pytest.raises(RuntimeError, match="sentinel"):
        b.inspect()


def test_mem0_silent_extraction_failure_is_loud():
    """The critical bug from Loop 2: Mem0 LLM extraction failure must surface
    as n_errors > 0 AND healthy=False AND last_error populated.
    """
    import os
    # Ensure ANTHROPIC_API_KEY is the placeholder (this is the failure mode)
    os.environ["ANTHROPIC_API_KEY"] = "placeholder-no-real-key"
    with tempfile.TemporaryDirectory() as td:
        b = Mem0Backend(config={"store_dir": td}, scope={"user_id": "test", "project": "honest_mem_silent"})
        if not b._health.healthy:
            pytest.skip(f"Mem0 init failed: {b._health.error_message}")
        ids = b.add(_make_substantive_turns())
        insp = b.inspect()
        # Either:
        #   (a) mem0 actually extracted facts (real API key was somehow set) — fine
        #   (b) extraction failed silently — we MUST detect it
        if ids:
            # Real success path; nothing to check
            return
        # Empty result on substantive input → must be flagged
        assert insp["n_errors"] >= 1, f"silent failure not flagged: {insp}"
        assert insp["healthy"] is False, f"backend still reports healthy after silent failure: {insp}"
        assert insp["last_error"] is not None
        assert insp["n_silent_extraction_failures"] >= 1
        # And n_memories must NOT be -1
        assert insp["n_memories"] >= 0


def test_record_error_centralized_contract():
    """Direct test of _record_error invariants."""
    b = NullBackend()
    assert b._health.healthy is True
    assert b._health.n_errors == 0

    b._record_error("test.op", "fake error", silent_extraction=True)

    assert b._health.healthy is False
    assert b._health.n_errors == 1
    assert b._health.last_error == "test.op: fake error"
    assert b._health.last_error_ts_utc > 0
    assert b._health.n_silent_extraction_failures == 1
    assert b._health.error_message == b._health.last_error


def test_record_error_non_silent():
    """A non-silent error increments n_errors but not n_silent_extraction_failures."""
    b = NullBackend()
    b._record_error("test.op", "transport failure")
    assert b._health.n_errors == 1
    assert b._health.n_silent_extraction_failures == 0
    assert b._health.healthy is False


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
