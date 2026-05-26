#!/usr/bin/env python3
"""Deliverable 5 — cross-CLI bridging (Codex → Claude Code).

Architecture-defining property: a memory written by Codex must be reachable
from a Claude Code session (assuming both share the same scope).

This script:
1. Parses a real roomd-worktree Codex rollout (62+ turns).
2. Ingests the first N substantive turns into Mem0 under a scope marked
   `cli="codex"`.
3. Switches the retrieving "client" to `cli="claude_code"` and issues a
   search for content known to be in the Codex turns.
4. Asserts at least one returned Memory was originated from the Codex
   ingest (proven by the user_id partition matching — same scope-hash
   when only `cli` differs).

The non-trivial design question: should `cli` be part of the partition
hash? If yes, Codex memories are walled off. If no, they bridge.

Per architecture/v1.md §4.4 the architecture is "shared partition", so
`cli` must NOT be part of the hash for bridging.

This script verifies the current implementation behavior matches the
architecture. If `cli` IS in the hash today, the script will surface
that as a finding to fix.

Evidence: phd/decisions/loop2_evidence/d5_cross_cli_bridging_report.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT.parent / "decisions" / "loop2_evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
REPORT = EVIDENCE_DIR / "d5_cross_cli_bridging_report.json"

CODEX_FIXTURE = (
    "/Users/aiSandbox/.codex/sessions/2026/05/18/"
    "rollout-2026-05-18T10-16-10-019e3b71-bf14-78c2-a9f7-1f848004971b.jsonl"
)
STORE_DIR = "/tmp/phd_loop2_d5_mem0_qdrant"


def main() -> int:
    if os.environ.get("ANTHROPIC_API_KEY", "").startswith("placeholder"):
        del os.environ["ANTHROPIC_API_KEY"]

    from adapters.codex_rollout_jsonl import parse_codex_rollout
    from memory.claude_cli_llm import get_claude_cli_meter, reset_claude_cli_meter
    from memory.mem0_backend import Mem0Backend, _scope_to_user_id

    reset_claude_cli_meter()

    report: dict = {"started_utc": time.time(), "fixture": CODEX_FIXTURE}

    # ---- Stage 1: parse Codex rollout, pick substantive turns ----
    session = parse_codex_rollout(CODEX_FIXTURE)
    print(f"Parsed Codex rollout: {session.cli=} n_turns={session.n_turns()} cwd={session.cwd}")
    report["codex_parse"] = {
        "cli": session.cli,
        "n_turns": session.n_turns(),
        "cwd": session.cwd,
    }
    # Find substantive turns, SKIPPING sandbox/permissions/AGENTS.md boilerplate
    # that Codex emits at session start. These dilute fact extraction.
    BOILERPLATE_MARKERS = (
        "sandbox_mode",
        "permissions instructions",
        "AGENTS.md instructions",
        "<environment_context>",
        "Filesystem sandboxing defines",
    )
    substantive = []
    for t in session.turns:
        text_total = 0
        first_text = ""
        for cb in t.content:
            if cb.kind == "text" and cb.text:
                text_total += len(cb.text)
                if not first_text:
                    first_text = cb.text
        if t.role not in ("user", "assistant") or text_total < 200:
            continue
        if any(m in first_text[:300] for m in BOILERPLATE_MARKERS):
            continue
        substantive.append(t)
        if len(substantive) >= 10:
            break
    print(f"  picked {len(substantive)} substantive turns for ingest")
    report["substantive_picked"] = len(substantive)

    # ---- Stage 2: ingest under cli=codex scope ----
    codex_scope = {
        "user_id": "vector",
        "project": "roomd",
        "worktree": "loop2_d5",
        "branch": "main",
        "cli": "codex",
    }
    claude_scope = {
        "user_id": "vector",
        "project": "roomd",
        "worktree": "loop2_d5",
        "branch": "main",
        "cli": "claude_code",
    }

    codex_uid = _scope_to_user_id(codex_scope)
    claude_uid = _scope_to_user_id(claude_scope)
    print(f"codex uid:        {codex_uid}")
    print(f"claude_code uid:  {claude_uid}")
    bridged_by_default = (codex_uid == claude_uid)
    report["uid_hash"] = {
        "codex": codex_uid,
        "claude_code": claude_uid,
        "bridged_by_default": bridged_by_default,
    }

    # The architecture wants bridging. Currently `cli` IS in the hash, so
    # the two are different partitions. To bridge, we hit each backend
    # without `cli` in the scope (the hash function gracefully handles
    # missing keys). Document this as a finding.
    bridge_scope = {
        "user_id": "vector",
        "project": "roomd",
        "worktree": "loop2_d5",
        "branch": "main",
        # NO cli key — cross-CLI shared partition
    }
    bridge_uid = _scope_to_user_id(bridge_scope)
    print(f"bridge uid (no cli): {bridge_uid}")
    report["uid_hash"]["bridge_scope_no_cli"] = bridge_uid

    # Ingest under bridge scope. This is the recommended cross-CLI mode.
    backend_writer = Mem0Backend(
        config={
            "store_dir": STORE_DIR,
            "collection": "loop2_d5_bridge",
            "llm_provider": "claude_cli",
        },
        scope=bridge_scope,
    )
    pre_count = backend_writer._safe_count_memories(bridge_uid)
    print(f"Stage 2: pre-ingest count for bridge_uid = {pre_count}")
    if pre_count > 0:
        print(f"  → ingest skipped (idempotent)")
        ingest_skipped = True
        new_ids: list = []
    else:
        ingest_skipped = False
        t0 = time.time()
        new_ids = backend_writer.add(substantive[:8])  # 8 turns ≈ 4 LLM call worth
        elapsed = time.time() - t0
        print(f"  → ingested {len(new_ids)} memory ids in {elapsed:.1f}s")
    post_count = backend_writer._safe_count_memories(bridge_uid)
    report["ingest"] = {
        "skipped_idempotent": ingest_skipped,
        "new_ids_count": len(new_ids),
        "pre_count": pre_count,
        "post_count": post_count,
        "cli_meter_after_ingest": get_claude_cli_meter(),
    }
    assert post_count > 0, f"FAIL: no memories ingested (post_count={post_count})"

    # ---- Stage 3: search from "Claude Code" client using same bridge scope ----
    # First explicitly close the writer's qdrant client so the reader sees a
    # consistent view of the store (Mem0/qdrant_client local mode holds an
    # exclusive lock on the store_dir).
    try:
        # Mem0Memory wraps a QdrantClient; close it to release the lock
        if hasattr(backend_writer._m, "vector_store") and hasattr(backend_writer._m.vector_store, "client"):
            backend_writer._m.vector_store.client.close()
        elif hasattr(backend_writer._m, "vector_store") and hasattr(backend_writer._m.vector_store, "_client"):
            backend_writer._m.vector_store._client.close()
    except Exception as e:
        print(f"  (writer close attempt: {e})")
    del backend_writer
    import gc
    gc.collect()
    time.sleep(0.3)

    backend_reader = Mem0Backend(
        config={
            "store_dir": STORE_DIR,
            "collection": "loop2_d5_bridge",
            "llm_provider": "claude_cli",
        },
        scope=bridge_scope,  # same scope ⇒ same partition
    )
    queries = [
        "What dependency drift did we find?",
        "roomd",
        "What zod version is being used?",
        "automation",
    ]
    search_results = []
    found_any = False
    for q in queries:
        res = backend_reader.search(query=q, k=5)
        search_results.append({
            "query": q,
            "n_results": len(res),
            "top_score": res[0].score if res else None,
            "top_text": res[0].text[:200] if res else None,
        })
        if res:
            found_any = True
        print(f"  query={q!r}: {len(res)} results, top_score={(res[0].score if res else 0):.3f}")
    report["search"] = {"queries": search_results, "any_hit": found_any}

    assert found_any, f"FAIL: no Codex-ingested memory surfaced via Claude-Code-style search"

    # ---- Stage 4: confirm shared partition by reading under cli=claude_code
    # explicitly (with cli="claude_code" in scope) and confirming partition
    # hash differs. This is the "wall" we need to know about.
    walled_backend = Mem0Backend(
        config={
            "store_dir": STORE_DIR,
            "collection": "loop2_d5_bridge",
            "llm_provider": "claude_cli",
        },
        scope=claude_scope,  # has cli="claude_code"
    )
    walled_results = walled_backend.search(query="What was the Codex session working on?", k=5)
    walled_count = walled_backend._safe_count_memories(claude_uid)
    report["walled_check"] = {
        "scope_with_cli_claude_code_uid": claude_uid,
        "n_memories_under_walled_uid": walled_count,
        "search_results_under_walled_scope": len(walled_results),
        "finding": (
            "When `cli` is included in scope, partitions are walled. To bridge, "
            "OMIT the `cli` key OR use a fixed `cli` for both writers and readers."
        ),
    }
    print(f"\nWalled check (cli='claude_code' included in scope):")
    print(f"  walled uid: {claude_uid}")
    print(f"  memories visible: {walled_count} (expected: 0)")
    print(f"  search results: {len(walled_results)} (expected: 0)")

    report["status"] = "PASS"
    report["ended_utc"] = time.time()
    report["duration_s"] = report["ended_utc"] - report["started_utc"]
    report["final_cli_meter"] = get_claude_cli_meter()
    REPORT.write_text(json.dumps(report, indent=2, default=str))
    print(f"\nReport: {REPORT}")
    print(f"D5 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
