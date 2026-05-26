#!/usr/bin/env python3
"""Skill retriever — called from SKILL.md at session start.

Usage:
    python3 retriever.py --arm <arm_name> --query "<first user prompt>" --k <k>

Outputs a markdown block of retrieved memories, formatted for direct
injection into the session's system context.

Provenance: logs every call to `~/.roomd/mem_inject_log.jsonl`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Make the phd code importable when the skill is installed into ~/.claude/skills/
# Order of precedence:
#   1. $ROOMD_PHD_CODE_DIR  (explicit env override)
#   2. $HOME/github/claude_can_do_anything/distillation/phd/code  (default for Vector)
#   3. Path(__file__).parents[2] — works when the script lives at
#      ./injection/claude_code_skill/retriever.py within a phd/code checkout
ROOT_CANDIDATES = [
    os.environ.get("ROOMD_PHD_CODE_DIR"),
    str(Path.home() / "github" / "claude_can_do_anything" / "distillation" / "phd" / "code"),
    str(Path(__file__).resolve().parents[2]),
]
for _candidate in ROOT_CANDIDATES:
    if not _candidate:
        continue
    p = Path(_candidate)
    if (p / "memory" / "base.py").exists() and (p / "adapters" / "schema.py").exists():
        sys.path.insert(0, str(p))
        break
else:
    # Fallback to the historic behavior so error messages remain useful
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def _backend_factory(arm: str, scope: dict):
    """Instantiate the configured backend for a given arm.

    Optional env overrides (for eval-time backend configuration):
      ROOMD_MEM0_STORE_DIR  → Mem0 qdrant store directory
      ROOMD_MEM0_COLLECTION → Mem0 collection name
      ROOMD_LETTA_BASE_URL  → Letta server base URL
    """
    if arm == "null":
        from memory.null_backend import NullBackend
        return NullBackend(scope=scope)
    if arm == "random":
        from memory.random_backend import RandomBackend
        return RandomBackend(scope=scope)
    if arm == "mem0":
        from memory.mem0_backend import Mem0Backend
        cfg = {}
        if os.environ.get("ROOMD_MEM0_STORE_DIR"):
            cfg["store_dir"] = os.environ["ROOMD_MEM0_STORE_DIR"]
        if os.environ.get("ROOMD_MEM0_COLLECTION"):
            cfg["collection"] = os.environ["ROOMD_MEM0_COLLECTION"]
        return Mem0Backend(scope=scope, config=cfg or None)
    if arm == "letta":
        from memory.letta_backend import LettaBackend
        cfg = {}
        if os.environ.get("ROOMD_LETTA_BASE_URL"):
            cfg["base_url"] = os.environ["ROOMD_LETTA_BASE_URL"]
        return LettaBackend(scope=scope, config=cfg or None)
    if arm == "hindsight":
        from memory.hindsight_backend import HindsightBackend
        return HindsightBackend(scope=scope)
    if arm == "cognee":
        from memory.cognee_backend import CogneeBackend
        return CogneeBackend(scope=scope)
    raise ValueError(f"Unknown arm: {arm}")


def _log_injection(record: dict) -> None:
    log_dir = Path.home() / ".roomd"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "mem_inject_log.jsonl"
    with log_path.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default=os.environ.get("ROOMD_MEM_ARM", "null"))
    ap.add_argument("--query", required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument(
        "--scope-user-id", default=os.environ.get("USER", "vector")
    )
    ap.add_argument("--scope-project", default="roomd")
    ap.add_argument("--scope-worktree", default=os.environ.get("ROOMD_WORKTREE", "main"))
    ap.add_argument("--scope-branch", default=os.environ.get("ROOMD_BRANCH", "main"))
    ap.add_argument("--scope-cli", default="claude_code")
    args = ap.parse_args()

    scope = {
        "user_id": args.scope_user_id,
        "project": args.scope_project,
        "worktree": args.scope_worktree,
        "branch": args.scope_branch,
        "cli": args.scope_cli,
    }

    t0 = time.time()
    try:
        backend = _backend_factory(args.arm, scope)
    except Exception as e:
        # Bail gracefully: emit nothing visible to the model
        sys.stderr.write(
            f"[roomd-memory-retrieval] backend init failed: {type(e).__name__}: {e}\n"
        )
        _log_injection(
            {
                "ts_utc": time.time(),
                "arm": args.arm,
                "query": args.query,
                "k": args.k,
                "scope": scope,
                "status": "INIT-FAILED",
                "error": f"{type(e).__name__}: {e}",
                "latency_ms": int((time.time() - t0) * 1000),
            }
        )
        return 0

    health = backend.inspect()
    if not health.get("healthy"):
        sys.stderr.write(
            f"[roomd-memory-retrieval] backend unhealthy ({args.arm}): "
            f"{health.get('error_message')}\n"
        )
        _log_injection(
            {
                "ts_utc": time.time(),
                "arm": args.arm,
                "query": args.query,
                "k": args.k,
                "scope": scope,
                "status": "UNHEALTHY",
                "error_message": health.get("error_message"),
                "latency_ms": int((time.time() - t0) * 1000),
            }
        )
        return 0

    try:
        mems = backend.search(query=args.query, k=args.k)
    except Exception as e:
        sys.stderr.write(
            f"[roomd-memory-retrieval] search failed: {type(e).__name__}: {e}\n"
        )
        _log_injection(
            {
                "ts_utc": time.time(),
                "arm": args.arm,
                "query": args.query,
                "k": args.k,
                "scope": scope,
                "status": "SEARCH-FAILED",
                "error": f"{type(e).__name__}: {e}",
                "latency_ms": int((time.time() - t0) * 1000),
            }
        )
        return 0

    latency_ms = int((time.time() - t0) * 1000)

    # Log
    _log_injection(
        {
            "ts_utc": time.time(),
            "arm": args.arm,
            "query": args.query,
            "k": args.k,
            "scope": scope,
            "status": "OK",
            "n_results": len(mems),
            "memory_ids": [m.memory_id for m in mems],
            "top_score": mems[0].score if mems else None,
            "latency_ms": latency_ms,
        }
    )

    # Emit markdown block to stdout (this is what the skill injects)
    if not mems:
        print(f"## Relevant prior knowledge\n\n_(no memories found for arm `{args.arm}`)_")
        return 0
    print(f"## Relevant prior knowledge\n")
    print(f"Source: arm=`{args.arm}` k={args.k} latency={latency_ms}ms")
    print()
    for m in mems:
        snippet = (m.text or "").replace("\n", " ")[:300]
        print(f"- `[memory_id={m.memory_id} score={m.score:.3f}]` {snippet}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
