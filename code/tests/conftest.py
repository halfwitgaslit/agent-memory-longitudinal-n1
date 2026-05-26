"""Pytest configuration shared across the phd/code test suite.

Loop 4 G7 hygiene: Mem0's qdrant lock at ~/.mem0/migrations_qdrant persists
across in-process Mem0Backend instances even after explicit teardown. To
keep tests deterministic without forcing every Mem0Backend caller to use
subprocess isolation (G7 architectural fix is the Mem0SubprocessBackend in
memory/mem0_subprocess.py), we wipe the stale lock file before each test
that needs to instantiate Mem0Backend.

This is hygiene only — it does NOT bypass the structural cross-process
lock issue. The Phase 2 eval harness should use Mem0SubprocessBackend for
parallel arm execution; this conftest is for the test suite alone.
"""
from __future__ import annotations

from pathlib import Path

import pytest


_MEM0_QDRANT_LOCK = Path.home() / ".mem0" / "migrations_qdrant" / ".lock"


def _clear_mem0_qdrant_lock() -> bool:
    """Best-effort: remove the stale qdrant lock file. Returns True if removed."""
    if _MEM0_QDRANT_LOCK.exists():
        try:
            _MEM0_QDRANT_LOCK.unlink()
            return True
        except Exception:
            return False
    return False


@pytest.fixture(autouse=True)
def _mem0_lock_hygiene():
    """Clear ~/.mem0/migrations_qdrant/.lock before each test.

    This is autouse because the lock is global and any prior test (even
    one not directly using Mem0) could have left it stale. Cheap (a
    single stat + unlink). After the test we do NOT clear again — that's
    the next test's job, and clearing during a Mem0Backend's lifecycle
    would be racy.
    """
    _clear_mem0_qdrant_lock()
    yield
