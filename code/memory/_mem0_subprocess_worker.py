#!/usr/bin/env python3
"""Mem0SubprocessBackend worker.

Reads a single JSON envelope from stdin:
    {"op": "add"|"search"|"inspect"|"clear",
     "config": {...},
     "scope": {...},
     "payload": {...}}

Constructs a fresh Mem0Backend, runs the operation, writes a JSON result
to stdout, and exits. The subprocess exit releases the qdrant lock.

This script is invoked by Mem0SubprocessBackend in the parent process.
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import sys
import time
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[1]))


# Global cross-process mutex for the shared ~/.mem0/migrations_qdrant lock.
# We hold this for the entire op, releasing on subprocess exit (no leak).
# Using POSIX fcntl flock with a polling wait so we surface failures
# instead of deadlocking.
_GLOBAL_LOCK_PATH = Path.home() / ".mem0" / ".phd_mem0_subprocess_lock"
_GLOBAL_LOCK_TIMEOUT_S = 60.0


def _acquire_global_mem0_lock(timeout_s: float = _GLOBAL_LOCK_TIMEOUT_S):
    """Acquire an exclusive file lock so only one Mem0Backend init runs at a time.

    Returns the open file handle (caller must NOT close it before the op is
    done — close releases the lock). On timeout, raises TimeoutError.
    """
    _GLOBAL_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = open(_GLOBAL_LOCK_PATH, "w")
    deadline = time.time() + timeout_s
    while True:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fh.write(f"pid={os.getpid()} ts={time.time()}\n")
            fh.flush()
            return fh
        except OSError as e:
            if e.errno not in (errno.EAGAIN, errno.EWOULDBLOCK):
                raise
            if time.time() >= deadline:
                fh.close()
                raise TimeoutError(
                    f"could not acquire {_GLOBAL_LOCK_PATH} within {timeout_s}s"
                )
            time.sleep(0.1)


def _err(msg: str, exc: BaseException | None = None) -> dict:
    return {
        "ok": False,
        "error": msg,
        "exc": (str(exc) if exc else None),
        "traceback": (traceback.format_exc() if exc else None),
    }


def main() -> int:
    try:
        envelope = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps(_err("bad stdin JSON", e)))
        return 1

    op = envelope.get("op")
    cfg = envelope.get("config") or {}
    scope = envelope.get("scope") or {}
    payload = envelope.get("payload") or {}

    try:
        from memory.mem0_backend import Mem0Backend
        from adapters.schema import Turn
    except Exception as e:
        print(json.dumps(_err("imports failed", e)))
        return 1

    # G7: serialize Mem0Backend init across processes via a global file lock.
    # Held for the duration of this subprocess. Released on exit.
    try:
        _lock_fh = _acquire_global_mem0_lock()
    except TimeoutError as e:
        print(json.dumps(_err("global mem0 lock timeout", e)))
        return 1

    try:
        b = Mem0Backend(config=cfg, scope=scope)
    except Exception as e:
        print(json.dumps(_err("Mem0Backend init failed", e)))
        return 1

    if not b._health.healthy:
        # Still emit a structured response so the parent can record it
        print(json.dumps({
            "ok": False,
            "error": b._health.error_message,
            "health": {
                "healthy": False,
                "error_message": b._health.error_message,
                "n_memories": b._health.n_memories,
            },
        }))
        return 0

    try:
        if op == "add":
            turns = [Turn(**t) for t in payload.get("turns", []) or []]
            scope_override = payload.get("scope_override")
            ids = b.add(turns, scope=scope_override) or []
            insp = b.inspect()
            print(json.dumps({
                "ok": True,
                "ids": ids,
                "health": {
                    "healthy": insp.get("healthy"),
                    "error_message": insp.get("error_message"),
                    "n_memories": insp.get("n_memories"),
                    "n_errors": insp.get("n_errors"),
                    "last_error": insp.get("last_error"),
                },
            }))
        elif op == "search":
            mems = b.search(
                query=payload.get("query", ""),
                k=int(payload.get("k", 5)),
                scope=payload.get("scope_override"),
            ) or []
            insp = b.inspect()
            print(json.dumps({
                "ok": True,
                "memories": [m.model_dump() for m in mems],
                "health": {
                    "healthy": insp.get("healthy"),
                    "n_memories": insp.get("n_memories"),
                },
            }))
        elif op == "inspect":
            insp = b.inspect()
            print(json.dumps({"ok": True, "health": insp}))
        elif op == "clear":
            b.clear()
            print(json.dumps({"ok": True}))
        else:
            print(json.dumps(_err(f"unknown op {op}")))
            return 1
    except Exception as e:
        print(json.dumps(_err(f"{op} raised", e)))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
