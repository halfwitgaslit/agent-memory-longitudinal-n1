"""Unified Turn/Session schema (Pydantic v2, versioned).

DESIGN CONTRACT (locked in architecture/v1.md §4.1):
- Lossless round-trip on metadata. Free-form content may be normalized, but
  the original record is preserved in `_raw`.
- `_schema_version` is bumped on any breaking change.
- All timestamps are unix seconds UTC (float).
- All identifiers are stable: turn_id = sha1(session_id, ordinal, content_hash).

This schema is consumed by:
- memory/* backends (via MemoryBackend.add(turns: List[Turn]))
- eval/* (for metrics computation on real sessions)
- injection/* (for replay)
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "v1.0"


class ContentBlock(BaseModel):
    """A single content block within a Turn.

    Mirrors Anthropic message content blocks (text, tool_use, tool_result, thinking).
    Codex `response_item.payload.content[]` is normalized into this same form.
    """

    model_config = ConfigDict(extra="allow")
    kind: Literal["text", "tool_use", "tool_result", "thinking", "image", "other"]
    text: Optional[str] = None
    name: Optional[str] = None  # tool name for tool_use
    input: Optional[Dict[str, Any]] = None  # tool_use input
    output: Optional[str] = None  # tool_result string output
    tool_use_id: Optional[str] = None
    is_error: Optional[bool] = None


class ToolEvent(BaseModel):
    """A complete tool_use / tool_result pair (post-correlation)."""

    model_config = ConfigDict(extra="allow")
    tool_use_id: str
    tool_name: str
    input: Dict[str, Any]
    output: Optional[str] = None
    is_error: Optional[bool] = None
    duration_ms: Optional[int] = None
    parent_turn_id: Optional[str] = None


class MemoryEvent(BaseModel):
    """An observed memory-system interaction within a session (for replay / metrics)."""

    model_config = ConfigDict(extra="allow")
    kind: Literal["search", "add", "promote", "decay", "inject"]
    ts_utc: float
    memory_ids: List[str] = Field(default_factory=list)
    backend: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class Turn(BaseModel):
    """A single conversational turn within a session."""

    model_config = ConfigDict(extra="allow")
    turn_id: str
    session_id: str
    ordinal: int
    role: Literal["user", "assistant", "system", "tool"]
    content: List[ContentBlock] = Field(default_factory=list)
    tool_events: List[ToolEvent] = Field(default_factory=list)
    ts_utc: float
    model: Optional[str] = None
    cli: Literal["claude_code", "codex"]
    worktree_id: Optional[str] = None
    parent_branch: Optional[str] = None
    parent_turn_id: Optional[str] = None
    _raw_records: List[Dict[str, Any]] = []
    _schema_version: str = SCHEMA_VERSION

    @staticmethod
    def make_turn_id(session_id: str, ordinal: int, content_text: str) -> str:
        h = hashlib.sha1()
        h.update(session_id.encode("utf-8", errors="replace"))
        h.update(b"\x1f")
        h.update(str(ordinal).encode())
        h.update(b"\x1f")
        h.update(content_text[:1024].encode("utf-8", errors="replace"))
        return h.hexdigest()[:16]


class Session(BaseModel):
    """A complete session (a single JSONL file's worth of turns)."""

    model_config = ConfigDict(extra="allow")
    session_id: str
    cli: Literal["claude_code", "codex"]
    source_path: str  # absolute path to the JSONL file
    project_dir: Optional[str] = None  # decoded project directory
    cwd: Optional[str] = None
    worktree_id: Optional[str] = None
    parent_branch: Optional[str] = None
    started_utc: Optional[float] = None
    ended_utc: Optional[float] = None
    turns: List[Turn] = Field(default_factory=list)
    base_instructions: Optional[str] = None
    cli_version: Optional[str] = None
    model_provider: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    _raw_records: List[Dict[str, Any]] = []
    _schema_version: str = SCHEMA_VERSION

    def to_jsonl(self) -> str:
        """Serialize as a single-line JSON dict (NOT the original CLI format)."""
        return self.model_dump_json(exclude={"_raw_records"}, exclude_none=False)

    def n_turns(self) -> int:
        return len(self.turns)

    def n_tool_events(self) -> int:
        return sum(len(t.tool_events) for t in self.turns)

    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "cli": self.cli,
            "n_turns": self.n_turns(),
            "n_tool_events": self.n_tool_events(),
            "source_path": self.source_path,
            "worktree_id": self.worktree_id,
            "started_utc": self.started_utc,
            "ended_utc": self.ended_utc,
        }


def hash_content_block(block: ContentBlock) -> str:
    """Stable hash of a content block for round-trip checks."""
    payload = block.model_dump(exclude_none=True)
    s = json.dumps(payload, sort_keys=True)
    return hashlib.sha1(s.encode("utf-8", errors="replace")).hexdigest()[:16]
