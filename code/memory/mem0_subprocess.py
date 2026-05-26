"""Loop 4 G7 — Mem0SubprocessBackend: subprocess-isolated Mem0Backend.

The qdrant on-disk store under ~/.mem0/migrations_qdrant uses an OS-level
exclusive file lock. Two Python processes cannot both hold a Mem0Backend
instance at the same time. Worse: within ONE process, instantiating a
second Mem0Backend (even after closing the first) fails because the
lock is not reliably released until process exit.

This wrapper exposes the same MemoryBackend surface as Mem0Backend, but
each call (add / search / inspect / clear) spawns a short-lived
subprocess. The subprocess:

  1. Constructs a fresh Mem0Backend with the wrapper's config/scope.
  2. Runs the requested operation.
  3. Serializes the result to stdout (JSON).
  4. Exits — releasing the qdrant lock.

This makes concurrent processes possible (each runs an independent
short-lived backend) and removes the "no two Mem0Backends in one
process" constraint at the cost of ~200-300ms overhead per call from
the venv warm-up.

Trade-offs documented in code comments and in
decisions/loop4_evidence/g7_subprocess_isolation.md.

Usage:
    from memory.mem0_subprocess import Mem0SubprocessBackend
    b = Mem0SubprocessBackend(scope={"user_id": "vector", ...})
    b.add(turns)
    b.search("query")

This is intended for the Phase 2 eval harness where parallelism is
required. For single-process smoke tests, Mem0Backend (direct) is faster.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.schema import Turn

from .base import Memory, MemoryBackend


_THIS_DIR = Path(__file__).resolve().parent
_PHD_CODE = _THIS_DIR.parent
_DEFAULT_VENV_PYTHON = _PHD_CODE / ".venv" / "bin" / "python"
_WORKER = _THIS_DIR / "_mem0_subprocess_worker.py"


class Mem0SubprocessBackend(MemoryBackend):
    """Subprocess-isolated Mem0 wrapper.

    Same interface as Mem0Backend. Each operation spawns a worker process.
    Suitable when multiple processes need to operate on the same store
    (sequentially or with per-scope qdrant paths).
    """

    backend_name = "mem0_subprocess"

    DEFAULT_TIMEOUT_S = 90.0

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        scope: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(config, scope)
        # Resolve the worker's interpreter (must have the phd venv to import mem0).
        self._python = Path(
            self.config.get("python")
            or os.environ.get("ROOMD_PHD_VENV_PYTHON", str(_DEFAULT_VENV_PYTHON))
        )
        if not self._python.exists():
            self._python = Path(sys.executable)  # last resort
        self._timeout_s = float(self.config.get("timeout_s", self.DEFAULT_TIMEOUT_S))
        # The subprocess is treated as the source of truth for healthy;
        # we mark ourselves healthy and let each operation surface its own
        # error in last_error if the subprocess fails.
        self._health.healthy = True
        self._health.embedding_model = "mem0-subprocess(fastembed-bge-small)"
        self._health.extra["worker_path"] = str(_WORKER)
        self._health.extra["python"] = str(self._python)

    # ------------------------------------------------------------------
    # Subprocess plumbing

    def _call_worker(self, op: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run the worker for a single op; return parsed JSON or raise."""
        envelope = {
            "op": op,
            "config": dict(self.config),
            "scope": dict(self.scope),
            "payload": payload,
        }
        try:
            proc = subprocess.run(
                [str(self._python), str(_WORKER)],
                input=json.dumps(envelope).encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            self._record_error(
                f"mem0_subprocess.{op}",
                f"timeout after {self._timeout_s}s",
            )
            return {"ok": False, "error": f"timeout: {e}"}
        if proc.returncode != 0:
            self._record_error(
                f"mem0_subprocess.{op}",
                f"rc={proc.returncode} stderr={proc.stderr[:400]!r}",
            )
            return {"ok": False, "error": proc.stderr.decode("utf-8", errors="replace")[:400]}
        try:
            return json.loads(proc.stdout.decode("utf-8"))
        except Exception as e:
            self._record_error(
                f"mem0_subprocess.{op}",
                f"json decode: {e}; stdout={proc.stdout[:200]!r}",
            )
            return {"ok": False, "error": f"json decode failure: {e}"}

    # ------------------------------------------------------------------
    # MemoryBackend interface

    def add(self, turns: List[Turn], scope: Optional[Dict[str, Any]] = None) -> List[str]:
        payload = {
            "turns": [t.model_dump() for t in turns],
            "scope_override": dict(scope) if scope else None,
        }
        res = self._call_worker("add", payload)
        if not res.get("ok"):
            return []
        ids = res.get("ids", []) or []
        # Propagate the worker's health view into ours so inspect() is useful.
        health = res.get("health") or {}
        if "n_memories" in health:
            self._health.n_memories = int(health["n_memories"])
        if health.get("error_message"):
            self._health.error_message = health["error_message"]
        self._health.n_adds += 1
        return [str(i) for i in ids]

    def search(
        self,
        query: str,
        k: int = 5,
        scope: Optional[Dict[str, Any]] = None,
    ) -> List[Memory]:
        payload = {
            "query": query,
            "k": int(k),
            "scope_override": dict(scope) if scope else None,
        }
        res = self._call_worker("search", payload)
        self._health.n_searches += 1
        if not res.get("ok"):
            return []
        out: List[Memory] = []
        for m in res.get("memories", []) or []:
            out.append(Memory(**m))
        # Refresh health from worker
        health = res.get("health") or {}
        if "n_memories" in health:
            self._health.n_memories = int(health["n_memories"])
        return out

    def inspect(self) -> Dict[str, Any]:
        # Optionally refresh n_memories from a worker call
        if self.config.get("refresh_inspect_in_worker", False):
            res = self._call_worker("inspect", {})
            if res.get("ok"):
                health = res.get("health") or {}
                if "n_memories" in health:
                    self._health.n_memories = int(health["n_memories"])
        return super().inspect()

    def clear(self) -> None:
        self._call_worker("clear", {})
        self._health.n_memories = 0
