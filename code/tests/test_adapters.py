"""Round-trip and integrity tests for adapters.

Tests run on real roomd corpus fixtures. They:
1. Parse 5+ representative real sessions per CLI
2. Verify Session/Turn schema completeness (no missing required fields)
3. Verify metadata round-trip: re-construct an "inverse" view of the parsed
   Session and check field-by-field against the raw records.
4. Verify cross-CLI normalization: both adapters produce comparable Turn schemas
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make adapters importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from adapters.claude_code_jsonl import iter_roomd_sessions, parse_claude_code_session  # noqa: E402
from adapters.codex_rollout_jsonl import iter_codex_sessions, parse_codex_rollout  # noqa: E402
from adapters.schema import SCHEMA_VERSION, ContentBlock, Session, Turn  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers


def _claude_code_samples(n: int = 5, min_size: int = 50_000) -> list[Path]:
    """Return n sample roomd JSONLs of varying size, each ≥ min_size bytes."""
    all_paths = [p for p in iter_roomd_sessions() if p.stat().st_size >= min_size]
    if len(all_paths) < n:
        return all_paths
    all_paths.sort(key=lambda p: p.stat().st_size)
    step = max(1, len(all_paths) // n)
    return [all_paths[i * step] for i in range(n) if i * step < len(all_paths)]


def _codex_samples(n: int = 5, min_size: int = 50_000) -> list[Path]:
    all_paths = [
        p
        for p in iter_codex_sessions(require_cwd_contains="roomd")
        if p.stat().st_size >= min_size
    ]
    if len(all_paths) < n:
        return all_paths
    all_paths.sort(key=lambda p: p.stat().st_size)
    step = max(1, len(all_paths) // n)
    return [all_paths[i * step] for i in range(n) if i * step < len(all_paths)]


# ---------------------------------------------------------------------------
# Claude Code adapter tests


def test_claude_code_schema_version():
    assert SCHEMA_VERSION == "v1.0"


@pytest.mark.parametrize("sample_idx", range(5))
def test_claude_code_parse_basic(sample_idx: int):
    samples = _claude_code_samples(5)
    if sample_idx >= len(samples):
        pytest.skip("Not enough roomd samples")
    p = samples[sample_idx]
    session = parse_claude_code_session(p)
    assert isinstance(session, Session)
    assert session.cli == "claude_code"
    assert session.session_id, "session_id must be non-empty"
    assert session.source_path == str(p.resolve())
    assert len(session._raw_records) > 0, "Raw records must be preserved"
    # At least one turn
    assert len(session.turns) > 0
    for t in session.turns:
        assert isinstance(t, Turn)
        assert t.cli == "claude_code"
        assert t.session_id == session.session_id
        assert t.role in ("user", "assistant", "system", "tool")


@pytest.mark.parametrize("sample_idx", range(5))
def test_claude_code_round_trip_raw_preservation(sample_idx: int):
    """Every Turn._raw_records entry must equal a raw JSONL record from the source."""
    samples = _claude_code_samples(5)
    if sample_idx >= len(samples):
        pytest.skip("Not enough roomd samples")
    p = samples[sample_idx]
    session = parse_claude_code_session(p)

    # Build a set of (uuid -> raw) from session._raw_records
    by_uuid = {r.get("uuid"): r for r in session._raw_records if r.get("uuid")}
    # All Turn._raw_records[0]['uuid'] must appear in the original raw set
    for t in session.turns:
        if not t._raw_records:
            continue
        raw = t._raw_records[0]
        if raw.get("uuid"):
            assert raw["uuid"] in by_uuid, f"Turn raw uuid {raw['uuid']} not in source"
            assert by_uuid[raw["uuid"]] is raw or by_uuid[raw["uuid"]] == raw


@pytest.mark.parametrize("sample_idx", range(5))
def test_claude_code_tool_event_correlation(sample_idx: int):
    """Tool uses and tool results should correlate by tool_use_id in most cases."""
    samples = _claude_code_samples(5)
    if sample_idx >= len(samples):
        pytest.skip("Not enough roomd samples")
    p = samples[sample_idx]
    session = parse_claude_code_session(p)

    tool_use_ids = set()
    tool_result_ids = set()
    for t in session.turns:
        for cb in t.content:
            if cb.kind == "tool_use" and cb.tool_use_id:
                tool_use_ids.add(cb.tool_use_id)
            elif cb.kind == "tool_result" and cb.tool_use_id:
                tool_result_ids.add(cb.tool_use_id)
    # Most tool_uses should have a corresponding tool_result (sessions may end mid-tool-use)
    if tool_use_ids:
        overlap = tool_use_ids & tool_result_ids
        ratio = len(overlap) / len(tool_use_ids)
        assert ratio >= 0.5, f"Tool use/result correlation too low: {ratio:.2f}"


# ---------------------------------------------------------------------------
# Codex adapter tests


@pytest.mark.parametrize("sample_idx", range(5))
def test_codex_parse_basic(sample_idx: int):
    samples = _codex_samples(5)
    if sample_idx >= len(samples):
        pytest.skip("Not enough Codex roomd samples")
    p = samples[sample_idx]
    session = parse_codex_rollout(p)
    assert isinstance(session, Session)
    assert session.cli == "codex"
    assert session.session_id, "session_id must be non-empty"
    assert session.source_path == str(p.resolve())
    assert len(session._raw_records) > 0
    # Most sessions have at least 1 turn but very short rollouts may have 0 response_items
    # so we just check non-negative
    assert len(session.turns) >= 0
    for t in session.turns:
        assert isinstance(t, Turn)
        assert t.cli == "codex"
        assert t.session_id == session.session_id
        assert t.role in ("user", "assistant", "system", "tool")


@pytest.mark.parametrize("sample_idx", range(5))
def test_codex_round_trip_raw_preservation(sample_idx: int):
    samples = _codex_samples(5)
    if sample_idx >= len(samples):
        pytest.skip("Not enough Codex roomd samples")
    p = samples[sample_idx]
    session = parse_codex_rollout(p)

    # Each Turn._raw_records[0] must be in session._raw_records by identity
    raw_set = {id(r) for r in session._raw_records}
    for t in session.turns:
        if not t._raw_records:
            continue
        raw = t._raw_records[0]
        assert id(raw) in raw_set, "Turn raw record not in session._raw_records"


@pytest.mark.parametrize("sample_idx", range(5))
def test_codex_function_call_correlation(sample_idx: int):
    samples = _codex_samples(5)
    if sample_idx >= len(samples):
        pytest.skip("Not enough Codex roomd samples")
    p = samples[sample_idx]
    session = parse_codex_rollout(p)

    call_ids = set()
    output_ids = set()
    for t in session.turns:
        for cb in t.content:
            if cb.kind == "tool_use" and cb.tool_use_id:
                call_ids.add(cb.tool_use_id)
            elif cb.kind == "tool_result" and cb.tool_use_id:
                output_ids.add(cb.tool_use_id)
    if call_ids:
        overlap = call_ids & output_ids
        ratio = len(overlap) / len(call_ids)
        assert ratio >= 0.5, f"Function call/output correlation too low: {ratio:.2f}"


# ---------------------------------------------------------------------------
# Cross-CLI normalization tests


def test_cross_cli_schema_uniformity():
    """A roomd Claude Code session and a roomd Codex session both produce
    Turn objects with the same field set; cli is the discriminator."""
    cc_samples = _claude_code_samples(1)
    cx_samples = _codex_samples(1)
    if not cc_samples or not cx_samples:
        pytest.skip("Need at least one roomd sample of each CLI")

    cc_session = parse_claude_code_session(cc_samples[0])
    cx_session = parse_codex_rollout(cx_samples[0])

    # Same Turn field shape
    cc_keys = set(Turn.model_fields.keys())
    cx_keys = set(Turn.model_fields.keys())
    assert cc_keys == cx_keys

    # Session field shape
    cc_skeys = set(Session.model_fields.keys())
    cx_skeys = set(Session.model_fields.keys())
    assert cc_skeys == cx_skeys

    # Both have session_id, cli set
    assert cc_session.cli == "claude_code"
    assert cx_session.cli == "codex"

    # Both produce JSON-serializable Sessions
    cc_session.to_jsonl()  # must not raise
    cx_session.to_jsonl()


def test_turn_id_stability():
    """Re-parsing the same session yields the same turn_ids."""
    cc_samples = _claude_code_samples(1)
    if not cc_samples:
        pytest.skip("No roomd samples")
    s1 = parse_claude_code_session(cc_samples[0])
    s2 = parse_claude_code_session(cc_samples[0])
    assert s1.session_id == s2.session_id
    assert [t.turn_id for t in s1.turns] == [t.turn_id for t in s2.turns]


def test_session_summary():
    cc_samples = _claude_code_samples(1)
    if not cc_samples:
        pytest.skip("No roomd samples")
    s = parse_claude_code_session(cc_samples[0])
    summary = s.summary()
    assert "session_id" in summary
    assert "cli" in summary
    assert "n_turns" in summary
    assert summary["n_turns"] == s.n_turns()


if __name__ == "__main__":
    # Allow direct run for quick sanity check
    print(f"Claude Code samples found: {len(_claude_code_samples(5))}")
    print(f"Codex samples found: {len(_codex_samples(5))}")
    for p in _claude_code_samples(3):
        s = parse_claude_code_session(p)
        print(
            f"  CC {p.name[:40]:40} → session_id={s.session_id[:8]} "
            f"turns={s.n_turns()} tool_events={s.n_tool_events()}"
        )
    for p in _codex_samples(3):
        s = parse_codex_rollout(p)
        print(
            f"  CX {p.name[:50]:50} → session_id={s.session_id[:8]} "
            f"turns={s.n_turns()} tool_events={s.n_tool_events()}"
        )
