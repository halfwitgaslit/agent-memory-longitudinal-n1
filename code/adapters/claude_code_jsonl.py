"""Claude Code JSONL adapter — parses a single session JSONL into a unified Session.

Source schema (observed empirically across roomd corpus, 176 sessions):
- Record types: user, assistant, system, attachment, queue-operation, last-prompt,
  ai-title, pr-link
- Top-level fields commonly observed: parentUuid, isSidechain, type, message, uuid,
  timestamp (ISO8601 Z), promptId, userType, entrypoint, cwd, sessionId, version,
  gitBranch, requestId, attributionSkill, isMeta, attachment, operation, content,
  toolUseResult, toolUseID, hookCount, hookInfos, hookErrors, preventedContinuation,
  stopReason, hasOutput, level, subtype, leafUuid, lastPrompt, aiTitle, prUrl,
  prRepository, prNumber, permissionMode, sourceToolAssistantUUID
- message.content can be either a string (early-format user prompts) or a list of
  content blocks {type: text|tool_use|tool_result|thinking|image, ...}.

ROUND-TRIP CONTRACT:
- Every original record is preserved in Session._raw_records and in the per-Turn
  _raw_records.
- The adapter is read-only; we never modify the JSONL file.
- Re-serializing via Session.to_jsonl() yields a NEW unified format; the round-trip
  test asserts that round-tripping a parsed Session through our format and back via
  the inverse (a small re-serializer) preserves all metadata fields.

NOT in scope:
- Modifying or generating Claude Code JSONL (we are read-only consumers).
- Cross-session linking (handled by eval/runner.py).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .schema import ContentBlock, Session, ToolEvent, Turn


def _parse_ts(ts: Optional[str]) -> float:
    """Parse ISO8601-Z timestamp into UTC unix seconds."""
    if not ts:
        return 0.0
    try:
        # Z form
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return 0.0


def _normalize_content(raw_content: Any) -> List[ContentBlock]:
    """Normalize a Claude Code message.content into ContentBlocks.

    Handles:
    - str (early-format simple user prompt)
    - list[dict] (standard content-blocks list)
    - None
    """
    if raw_content is None:
        return []
    if isinstance(raw_content, str):
        return [ContentBlock(kind="text", text=raw_content)]
    if not isinstance(raw_content, list):
        # Unknown shape — preserve as text repr
        return [ContentBlock(kind="other", text=repr(raw_content))]
    blocks: List[ContentBlock] = []
    for cb in raw_content:
        if not isinstance(cb, dict):
            blocks.append(ContentBlock(kind="other", text=str(cb)))
            continue
        ct = cb.get("type", "other")
        if ct == "text":
            blocks.append(ContentBlock(kind="text", text=cb.get("text", "")))
        elif ct == "thinking":
            blocks.append(
                ContentBlock(kind="thinking", text=cb.get("thinking", ""))
            )
        elif ct == "tool_use":
            blocks.append(
                ContentBlock(
                    kind="tool_use",
                    name=cb.get("name"),
                    input=cb.get("input") or {},
                    tool_use_id=cb.get("id"),
                )
            )
        elif ct == "tool_result":
            output = cb.get("content")
            if isinstance(output, list):
                # Sometimes tool_result.content is a list of {type:text,text:...}
                parts: List[str] = []
                for sub in output:
                    if isinstance(sub, dict) and sub.get("type") == "text":
                        parts.append(sub.get("text", ""))
                    else:
                        parts.append(str(sub))
                output_str = "\n".join(parts)
            else:
                output_str = output if isinstance(output, str) else json.dumps(output)
            blocks.append(
                ContentBlock(
                    kind="tool_result",
                    output=output_str,
                    tool_use_id=cb.get("tool_use_id"),
                    is_error=bool(cb.get("is_error", False)),
                )
            )
        elif ct in ("image",):
            blocks.append(ContentBlock(kind="image", text=cb.get("source", {}).get("media_type", "image")))
        else:
            # Preserve unknown content as 'other'
            blocks.append(ContentBlock(kind="other", text=json.dumps(cb)[:1000]))
    return blocks


def _decode_project_dir(jsonl_dir: Path) -> Optional[str]:
    """Decode the project_dir from the Claude Code project directory name.

    Convention (per session_inspector empirically): the directory under
    `~/.claude/projects/` is the absolute project path with `/`, `.`, `_`
    replaced by `-`. We can heuristically reverse this for a hint, but the
    exact original may be ambiguous. We return the original directory string
    with a leading `/` re-attached if it starts with a leading hyphen.
    """
    name = jsonl_dir.name
    if name.startswith("-"):
        # The convention prefixes with `-` for the leading `/`
        return "/" + name[1:].replace("-", "/")
    return name


def parse_claude_code_session(jsonl_path: str | Path) -> Session:
    """Parse a single Claude Code session JSONL into a Session.

    Idempotent + read-only. Lossless on metadata: every raw record is retained
    in Session._raw_records (and per-turn for user/assistant turns).
    """
    p = Path(jsonl_path)
    raw_records: List[Dict[str, Any]] = []
    with p.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                # Skip malformed lines; the JSONL files sometimes have partials at EOF
                continue
            raw_records.append(d)

    # Derive session metadata from the first record that has it
    session_id = ""
    cwd = None
    git_branch = None
    cli_version = None
    started_utc = None
    ended_utc = None

    for r in raw_records:
        if not session_id and r.get("sessionId"):
            session_id = r["sessionId"]
        if cwd is None and r.get("cwd"):
            cwd = r["cwd"]
        if git_branch is None and r.get("gitBranch"):
            git_branch = r["gitBranch"]
        if cli_version is None and r.get("version"):
            cli_version = r["version"]
        ts = _parse_ts(r.get("timestamp"))
        if ts > 0:
            if started_utc is None or ts < started_utc:
                started_utc = ts
            if ended_utc is None or ts > ended_utc:
                ended_utc = ts

    if not session_id:
        # Fallback: filename stem
        session_id = p.stem

    project_dir = _decode_project_dir(p.parent)
    worktree_id = None
    parent_branch = None
    if cwd:
        # Heuristic: if cwd contains `.claude/worktrees/` or `/worktrees/`,
        # the worktree slug is the last segment of the path.
        if "/worktrees/" in cwd:
            worktree_id = cwd.split("/worktrees/")[-1].split("/")[0]
        # parent_branch: try gitBranch; otherwise None
        if git_branch:
            parent_branch = git_branch

    # Build turns from user / assistant / system records
    turns: List[Turn] = []
    ordinal = 0
    pending_tool_uses: Dict[str, ToolEvent] = {}
    last_turn_id: Optional[str] = None

    for r in raw_records:
        rtype = r.get("type", "")
        if rtype not in ("user", "assistant", "system"):
            continue
        if rtype == "system":
            # System records (stop_hook_summary etc.) — preserve as system turn
            text = (
                f"[system subtype={r.get('subtype', '')} "
                f"level={r.get('level', '')} "
                f"stopReason={r.get('stopReason', '')!r}]"
            )
            turn_id = Turn.make_turn_id(session_id, ordinal, text)
            turn = Turn(
                turn_id=turn_id,
                session_id=session_id,
                ordinal=ordinal,
                role="system",
                content=[ContentBlock(kind="text", text=text)],
                tool_events=[],
                ts_utc=_parse_ts(r.get("timestamp")),
                model=None,
                cli="claude_code",
                worktree_id=worktree_id,
                parent_branch=parent_branch,
                parent_turn_id=last_turn_id,
            )
            turn._raw_records = [r]
            turns.append(turn)
            last_turn_id = turn_id
            ordinal += 1
            continue

        msg = r.get("message") or {}
        role = msg.get("role", rtype)
        raw_content = msg.get("content")
        blocks = _normalize_content(raw_content)

        # Aggregate visible text for stable turn_id
        text_for_id = ""
        for b in blocks:
            if b.kind == "text" and b.text:
                text_for_id += b.text
            elif b.kind == "tool_use":
                text_for_id += f"<tool_use:{b.name}>"
            elif b.kind == "tool_result":
                text_for_id += "<tool_result>"
        if not text_for_id:
            text_for_id = repr(raw_content)[:200]

        turn_id = Turn.make_turn_id(session_id, ordinal, text_for_id)

        # Correlate tool_use / tool_result pairs
        tool_events: List[ToolEvent] = []
        for b in blocks:
            if b.kind == "tool_use":
                te = ToolEvent(
                    tool_use_id=b.tool_use_id or "",
                    tool_name=b.name or "",
                    input=b.input or {},
                    parent_turn_id=turn_id,
                )
                if te.tool_use_id:
                    pending_tool_uses[te.tool_use_id] = te
                tool_events.append(te)
            elif b.kind == "tool_result":
                tuid = b.tool_use_id or ""
                pending = pending_tool_uses.pop(tuid, None)
                if pending is not None:
                    pending.output = b.output
                    pending.is_error = b.is_error
                    # Don't double-add to this turn's tool_events; it belongs to the
                    # tool_use turn, but for ease of replay we also embed a stub here
                tool_events.append(
                    ToolEvent(
                        tool_use_id=tuid,
                        tool_name=(pending.tool_name if pending else "<unmatched>"),
                        input=(pending.input if pending else {}),
                        output=b.output,
                        is_error=b.is_error,
                        parent_turn_id=turn_id,
                    )
                )

        # Role normalization: messages with role 'user' that contain only tool_result
        # blocks are tool turns, not user turns.
        normalized_role = role
        if (
            role == "user"
            and blocks
            and all(b.kind == "tool_result" for b in blocks)
        ):
            normalized_role = "tool"

        turn = Turn(
            turn_id=turn_id,
            session_id=session_id,
            ordinal=ordinal,
            role=normalized_role,  # type: ignore[arg-type]
            content=blocks,
            tool_events=tool_events,
            ts_utc=_parse_ts(r.get("timestamp")),
            model=msg.get("model"),
            cli="claude_code",
            worktree_id=worktree_id,
            parent_branch=parent_branch,
            parent_turn_id=last_turn_id,
        )
        turn._raw_records = [r]
        turns.append(turn)
        last_turn_id = turn_id
        ordinal += 1

    session = Session(
        session_id=session_id,
        cli="claude_code",
        source_path=str(p.resolve()),
        project_dir=project_dir,
        cwd=cwd,
        worktree_id=worktree_id,
        parent_branch=parent_branch,
        started_utc=started_utc,
        ended_utc=ended_utc,
        turns=turns,
        cli_version=cli_version,
        model_provider="anthropic",
        metadata={
            "n_raw_records": len(raw_records),
        },
    )
    session._raw_records = raw_records
    return session


def iter_roomd_sessions(
    projects_root: str | Path = "/Users/aiSandbox/.claude/projects",
    glob: str = "*roomd*",
) -> Iterator[Path]:
    """Yield all roomd-related Claude Code JSONL paths."""
    root = Path(projects_root)
    if not root.exists():
        return
    for project_dir in sorted(root.glob(glob)):
        if not project_dir.is_dir():
            continue
        for jsonl in sorted(project_dir.glob("*.jsonl")):
            if jsonl.stat().st_size > 0:
                yield jsonl
