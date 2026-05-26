"""Per-session metrics for the eval (architecture/v1.md §4.6).

Operates on a unified Session (from adapters.schema). For metrics that
require ground-truth labels (task_success_binary, task_success_5pt,
had_to_remind_count), the subject's manual entries are read from a
sidecar JSON file written by `phd_mem record-task --session-id <id>`.

The eval/runner.py module orchestrates: it loads sessions, merges with the
task-record sidecars, computes a MetricSet per session, and writes one
JSONL line per session into the results store.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from adapters.schema import Session, Turn


@dataclass
class MetricSet:
    """A complete per-session metric tuple for one arm."""

    session_id: str
    arm: str
    project: Optional[str] = None
    worktree: Optional[str] = None
    branch: Optional[str] = None
    time_of_day_bucket: Optional[str] = None
    cli: Optional[str] = None
    # Primary metrics
    task_success_binary: Optional[int] = None  # 0/1, from sidecar
    task_success_5pt: Optional[int] = None  # 1..5, from sidecar
    time_to_first_useful_output_s: Optional[float] = None
    # Secondary metrics
    total_session_duration_s: Optional[float] = None
    total_token_spend_usd: Optional[float] = None
    retry_count: int = 0
    had_to_remind_count: int = 0
    prior_knowledge_recall: Optional[float] = None  # 0..1, judge-labeled
    conflict_events: int = 0
    # Provenance
    n_turns: int = 0
    n_tool_events: int = 0
    raw_subject_notes: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = dict(self.__dict__)
        return d


# ---------------------------------------------------------------------------
# Time-of-day bucketing


def time_of_day_bucket(ts_utc: float, tz_offset_hours: float = -4.0) -> str:
    """Bucket a UTC timestamp into one of {morning,afternoon,evening,night} per the
    pre-registered design (eval/experimental_constants.py).

    tz_offset_hours: local time offset from UTC for the subject (default ET = -4).
    """
    if not ts_utc:
        return "unknown"
    local_ts = ts_utc + tz_offset_hours * 3600.0
    h = (int(local_ts) // 3600) % 24
    if 6 <= h < 12:
        return "morning_0600_1200"
    if 12 <= h < 18:
        return "afternoon_1200_1800"
    if 18 <= h < 24:
        return "evening_1800_0000"
    return "night_0000_0600"


# ---------------------------------------------------------------------------
# Reminder detection (regex; manual spot-check during paper review)


_REMINDER_PATTERNS = [
    re.compile(r"\bas I (?:told|said|mentioned)\b", re.IGNORECASE),
    re.compile(r"\b(?:you|please) (?:already )?(?:remember|forget|forgot)\b", re.IGNORECASE),
    re.compile(r"\bI (?:already|just) (?:told|said)\b", re.IGNORECASE),
    re.compile(r"\bdidn'?t I (?:tell|say|mention)\b", re.IGNORECASE),
    re.compile(r"\byou (?:always|keep) (?:forget|missing)\b", re.IGNORECASE),
    re.compile(r"\b(?:remember|recall) (?:that|when|how)\b", re.IGNORECASE),
]


def count_reminders(session: Session) -> int:
    """Count user turns containing reminder phrases."""
    n = 0
    for t in session.turns:
        if t.role != "user":
            continue
        for cb in t.content:
            if cb.kind != "text" or not cb.text:
                continue
            for pat in _REMINDER_PATTERNS:
                if pat.search(cb.text):
                    n += 1
                    break  # one reminder per turn max
            else:
                continue
            break
    return n


# ---------------------------------------------------------------------------
# Retry detection


def count_retries(session: Session) -> int:
    """Count tool_use events that appear to be retries of a previous failed call.

    Heuristic: same tool_name and similar input within 60 seconds of a previous
    is_error=True result.
    """
    n = 0
    recent_errors: Dict[str, float] = {}  # tool_name → ts of last error
    for t in session.turns:
        for te in t.tool_events:
            tname = te.tool_name
            ts = t.ts_utc
            if te.is_error:
                recent_errors[tname] = ts
                continue
            # tool_use (no output yet)
            if te.output is None and tname in recent_errors:
                if ts - recent_errors[tname] < 60.0:
                    n += 1
    return n


# ---------------------------------------------------------------------------
# Token-spend extraction (Claude Code JSONL has per-message usage)


def extract_token_spend_usd(session: Session) -> Optional[float]:
    """Extract approximate cost from session._raw_records' assistant `usage` fields.

    Pricing (approximate, Sonnet 4.5/4.6 standard tier):
      input: $3.00/MT, cache_creation: $3.75/MT, cache_read: $0.30/MT, output: $15.00/MT
    For Opus 4.7: input $15/MT, cache_creation $18.75/MT, cache_read $1.50/MT, output $75/MT
    For Haiku 4.5: input $0.80/MT, cache_creation $1.00/MT, cache_read $0.08/MT, output $4/MT

    NOTE: This is an approximation; actual cost varies by model-tier and
    billing window. Use for relative comparison only.
    """
    pricing = {
        "sonnet": {"in": 3.0, "cc": 3.75, "cr": 0.30, "out": 15.0},
        "opus": {"in": 15.0, "cc": 18.75, "cr": 1.50, "out": 75.0},
        "haiku": {"in": 0.80, "cc": 1.00, "cr": 0.08, "out": 4.0},
        "default": {"in": 3.0, "cc": 3.75, "cr": 0.30, "out": 15.0},
    }
    total = 0.0
    found_any = False
    for r in session._raw_records:
        if r.get("type") != "assistant":
            continue
        msg = r.get("message") or {}
        model = (msg.get("model") or "").lower()
        usage = msg.get("usage") or {}
        if not usage:
            continue
        family = "default"
        if "sonnet" in model:
            family = "sonnet"
        elif "opus" in model:
            family = "opus"
        elif "haiku" in model:
            family = "haiku"
        p = pricing[family]
        c = (
            (usage.get("input_tokens", 0) / 1e6) * p["in"]
            + (usage.get("cache_creation_input_tokens", 0) / 1e6) * p["cc"]
            + (usage.get("cache_read_input_tokens", 0) / 1e6) * p["cr"]
            + (usage.get("output_tokens", 0) / 1e6) * p["out"]
        )
        if c > 0:
            total += c
            found_any = True
    return total if found_any else None


# ---------------------------------------------------------------------------
# Time-to-first-useful-output


def time_to_first_useful_output_s(session: Session) -> Optional[float]:
    """Time from session start to the first assistant turn that contains
    non-thinking, non-empty text output."""
    if not session.turns or session.started_utc is None:
        return None
    for t in session.turns:
        if t.role != "assistant":
            continue
        for cb in t.content:
            if cb.kind == "text" and cb.text and cb.text.strip():
                return max(0.0, t.ts_utc - session.started_utc)
    return None


# ---------------------------------------------------------------------------
# Conflict detection (placeholder — full integration is Phase 3)


def count_conflict_events(session: Session) -> int:
    """Count session events flagged as a memory conflict.

    For now: count tool_results with is_error=True that reference a memory_id
    (a substring match on 'memory_id=' in the result). In Phase 3 we'll add
    explicit conflict-event logging from the retriever.
    """
    n = 0
    for t in session.turns:
        for cb in t.content:
            if cb.kind == "tool_result" and cb.is_error and cb.output:
                if "memory_id=" in cb.output[:1000]:
                    n += 1
    return n


# ---------------------------------------------------------------------------
# Top-level compute


def compute_session_metrics(
    session: Session,
    arm: str,
    task_record: Optional[Dict[str, Any]] = None,
) -> MetricSet:
    """Compute the full MetricSet for one session.

    task_record: optional sidecar dict from `phd_mem record-task` containing
    {task_success_binary, task_success_5pt, raw_notes, ...}.
    """
    ms = MetricSet(
        session_id=session.session_id,
        arm=arm,
        project=session.metadata.get("project") or session.project_dir,
        worktree=session.worktree_id,
        branch=session.parent_branch,
        cli=session.cli,
        n_turns=session.n_turns(),
        n_tool_events=session.n_tool_events(),
    )
    if session.started_utc:
        ms.time_of_day_bucket = time_of_day_bucket(session.started_utc)
        if session.ended_utc:
            ms.total_session_duration_s = max(0.0, session.ended_utc - session.started_utc)
    ms.time_to_first_useful_output_s = time_to_first_useful_output_s(session)
    ms.total_token_spend_usd = extract_token_spend_usd(session)
    ms.retry_count = count_retries(session)
    ms.had_to_remind_count = count_reminders(session)
    ms.conflict_events = count_conflict_events(session)
    if task_record:
        ms.task_success_binary = task_record.get("task_success_binary")
        ms.task_success_5pt = task_record.get("task_success_5pt")
        ms.raw_subject_notes = task_record.get("raw_notes")
        ms.prior_knowledge_recall = task_record.get("prior_knowledge_recall")
    return ms


def load_task_record(session_id: str, records_dir: str | Path) -> Optional[Dict[str, Any]]:
    """Read a task-record sidecar from disk."""
    p = Path(records_dir) / f"task_{session_id}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None
