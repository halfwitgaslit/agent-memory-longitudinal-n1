"""Adapters: convert raw CLI JSONL session logs into the unified Turn/Session schema.

Exports:
- schema.Turn, Session, ContentBlock, ToolEvent, MemoryEvent (Pydantic v2)
- claude_code_jsonl.parse_claude_code_session(path) -> Session
- codex_rollout_jsonl.parse_codex_rollout(path) -> Session
"""

from .schema import (
    ContentBlock,
    MemoryEvent,
    Session,
    ToolEvent,
    Turn,
    SCHEMA_VERSION,
)

__all__ = [
    "ContentBlock",
    "MemoryEvent",
    "Session",
    "ToolEvent",
    "Turn",
    "SCHEMA_VERSION",
]
