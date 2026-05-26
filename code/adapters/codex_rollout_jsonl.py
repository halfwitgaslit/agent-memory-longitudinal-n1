"""Codex rollout JSONL adapter — parses Codex session rollouts into unified Session.

Source schema (observed empirically across 924 sessions in
~/.codex/sessions/ and ~/.codex/archived_sessions/):

Top-level record types:
- session_meta: id, cwd, originator, cli_version, source, model_provider,
                base_instructions, optional forked_from_id, optional agent_nickname
- turn_context: per-turn metadata
- response_item: a single OpenAI-format message OR function_call OR
                 function_call_output OR reasoning OR custom_tool_call
- event_msg: lifecycle events (task_started, task_complete, token_count,
             exec_command_end, patch_apply_end, agent_message, user_message, ...)
- compacted: history compaction marker

Each record has top-level keys: {timestamp, type, payload}

payload (per type):
- session_meta.payload:
    id, timestamp, cwd, originator, cli_version, source ({user, subagent.thread_spawn:{...}}),
    model_provider, base_instructions (huge text), [forked_from_id], [agent_nickname]
- response_item.payload:
    type=message: role, content[{type:input_text|output_text|text, text}]
    type=function_call: name, arguments(json string), call_id
    type=function_call_output: call_id, output(string OR json-string of list)
    type=custom_tool_call: name, arguments, call_id
    type=custom_tool_call_output: call_id, output
    type=reasoning: summary, content, encrypted_content
- event_msg.payload:
    type=token_count: input_tokens, output_tokens, ...
    type=exec_command_end: stdout, stderr, exit_code, duration_ms
    type=task_started: ...
    type=task_complete: ...
    type=agent_message: ...
    type=user_message: ...

ROUND-TRIP CONTRACT (same as Claude Code adapter):
- All raw records preserved in Session._raw_records and per-Turn _raw_records.
- Read-only adapter; we never modify the JSONL file.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .schema import ContentBlock, Session, ToolEvent, Turn


def _parse_ts(ts: Optional[str]) -> float:
    if not ts:
        return 0.0
    try:
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts).timestamp()
    except Exception:
        return 0.0


def _normalize_message_content(raw_content: Any) -> List[ContentBlock]:
    """Codex stores message content as list[{type: input_text|output_text|text, text}]."""
    if raw_content is None:
        return []
    if isinstance(raw_content, str):
        return [ContentBlock(kind="text", text=raw_content)]
    if not isinstance(raw_content, list):
        return [ContentBlock(kind="other", text=repr(raw_content))]
    blocks: List[ContentBlock] = []
    for cb in raw_content:
        if not isinstance(cb, dict):
            blocks.append(ContentBlock(kind="other", text=str(cb)))
            continue
        ct = cb.get("type", "")
        if ct in ("input_text", "output_text", "text"):
            blocks.append(ContentBlock(kind="text", text=cb.get("text", "")))
        elif ct == "input_image":
            blocks.append(ContentBlock(kind="image", text=cb.get("image_url", "image")))
        else:
            blocks.append(ContentBlock(kind="other", text=json.dumps(cb)[:1000]))
    return blocks


def _parse_function_call_args(args_str: str) -> Dict[str, Any]:
    """Codex function_call.arguments is a JSON-encoded string."""
    if not args_str:
        return {}
    try:
        d = json.loads(args_str)
        if isinstance(d, dict):
            return d
        return {"_value": d}
    except Exception:
        return {"_raw": args_str[:2000]}


def _parse_function_call_output(out: Any) -> str:
    """Codex function_call_output.output is either a string or a JSON-encoded list of {type:text,text}."""
    if out is None:
        return ""
    if isinstance(out, str):
        # May be a JSON-encoded list[{type:text,text:...}]
        try:
            d = json.loads(out)
            if isinstance(d, list):
                parts: List[str] = []
                for x in d:
                    if isinstance(x, dict) and "text" in x:
                        parts.append(x["text"])
                    else:
                        parts.append(str(x))
                return "\n".join(parts)
        except Exception:
            pass
        return out
    return json.dumps(out)


def _derive_worktree_id(cwd: Optional[str]) -> Optional[str]:
    """Codex sessions often run under ~/.codex/worktrees/<id>/<project>/."""
    if not cwd:
        return None
    parts = cwd.split("/")
    if ".codex" in parts and "worktrees" in parts:
        i = parts.index("worktrees")
        if i + 1 < len(parts):
            return parts[i + 1]
    # Or under github/<repo>/worktrees/...
    if "worktrees" in parts:
        i = parts.index("worktrees")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


def parse_codex_rollout(jsonl_path: str | Path) -> Session:
    """Parse a single Codex rollout JSONL into a Session.

    Multiple session_meta records (e.g., on resume/fork) are kept in metadata.
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
                continue
            raw_records.append(d)

    # Extract session-level metadata from the first session_meta
    session_id = ""
    cwd = None
    cli_version = None
    started_utc: Optional[float] = None
    ended_utc: Optional[float] = None
    base_instructions: Optional[str] = None
    model_provider: Optional[str] = None
    originator: Optional[str] = None
    forked_from_id: Optional[str] = None
    agent_nickname: Optional[str] = None
    extra_session_metas: List[Dict[str, Any]] = []

    for r in raw_records:
        if r.get("type") == "session_meta":
            payload = r.get("payload") or {}
            if not session_id and payload.get("id"):
                session_id = payload["id"]
            if cwd is None and payload.get("cwd"):
                cwd = payload["cwd"]
            if cli_version is None and payload.get("cli_version"):
                cli_version = payload["cli_version"]
            if base_instructions is None and payload.get("base_instructions"):
                bi = payload["base_instructions"]
                if isinstance(bi, dict):
                    base_instructions = bi.get("text") or json.dumps(bi)[:5000]
                elif isinstance(bi, str):
                    base_instructions = bi
            if model_provider is None and payload.get("model_provider"):
                model_provider = payload["model_provider"]
            if originator is None and payload.get("originator"):
                originator = payload["originator"]
            if forked_from_id is None and payload.get("forked_from_id"):
                forked_from_id = payload["forked_from_id"]
            if agent_nickname is None and payload.get("agent_nickname"):
                agent_nickname = payload["agent_nickname"]
            if started_utc is None:
                ts = _parse_ts(r.get("timestamp"))
                if ts:
                    started_utc = ts
            extra_session_metas.append(payload)

        ts = _parse_ts(r.get("timestamp"))
        if ts:
            if started_utc is None or ts < started_utc:
                started_utc = ts
            if ended_utc is None or ts > ended_utc:
                ended_utc = ts

    if not session_id:
        session_id = p.stem

    worktree_id = _derive_worktree_id(cwd)
    parent_branch = None  # Codex doesn't carry git branch in metadata typically

    # Build turns: one Turn per response_item.payload.type=message (user/assistant)
    # OR per response_item.payload.type=function_call (assistant tool call).
    # function_call_output blocks are correlated into ToolEvents.
    turns: List[Turn] = []
    ordinal = 0
    last_turn_id: Optional[str] = None
    pending_tool_calls: Dict[str, ToolEvent] = {}

    for r in raw_records:
        rtype = r.get("type", "")
        payload = r.get("payload") or {}
        ptype = payload.get("type", "")
        ts = _parse_ts(r.get("timestamp"))

        if rtype != "response_item":
            # event_msg, turn_context, session_meta — preserve as raw on session level
            continue

        if ptype == "message":
            role = payload.get("role", "assistant")
            blocks = _normalize_message_content(payload.get("content"))
            text_for_id = " ".join(b.text for b in blocks if b.text)[:1024] or repr(payload)[:200]
            turn_id = Turn.make_turn_id(session_id, ordinal, text_for_id)
            turn = Turn(
                turn_id=turn_id,
                session_id=session_id,
                ordinal=ordinal,
                role="user" if role == "user" else "assistant",
                content=blocks,
                tool_events=[],
                ts_utc=ts,
                model=None,
                cli="codex",
                worktree_id=worktree_id,
                parent_branch=parent_branch,
                parent_turn_id=last_turn_id,
            )
            turn._raw_records = [r]
            turns.append(turn)
            last_turn_id = turn_id
            ordinal += 1
        elif ptype in ("function_call", "custom_tool_call"):
            name = payload.get("name", "")
            args = _parse_function_call_args(payload.get("arguments", ""))
            call_id = payload.get("call_id", "")
            te = ToolEvent(
                tool_use_id=call_id,
                tool_name=name,
                input=args,
                parent_turn_id=None,  # set below
            )
            text_for_id = f"<tool_use:{name}>"
            turn_id = Turn.make_turn_id(session_id, ordinal, text_for_id)
            te.parent_turn_id = turn_id
            pending_tool_calls[call_id] = te
            turn = Turn(
                turn_id=turn_id,
                session_id=session_id,
                ordinal=ordinal,
                role="assistant",
                content=[
                    ContentBlock(
                        kind="tool_use",
                        name=name,
                        input=args,
                        tool_use_id=call_id,
                    )
                ],
                tool_events=[te],
                ts_utc=ts,
                model=None,
                cli="codex",
                worktree_id=worktree_id,
                parent_branch=parent_branch,
                parent_turn_id=last_turn_id,
            )
            turn._raw_records = [r]
            turns.append(turn)
            last_turn_id = turn_id
            ordinal += 1
        elif ptype in ("function_call_output", "custom_tool_call_output"):
            call_id = payload.get("call_id", "")
            output = _parse_function_call_output(payload.get("output"))
            pending = pending_tool_calls.pop(call_id, None)
            te = ToolEvent(
                tool_use_id=call_id,
                tool_name=pending.tool_name if pending else "<unmatched>",
                input=pending.input if pending else {},
                output=output,
                is_error=False,  # Codex doesn't always flag errors at this layer
                parent_turn_id=None,
            )
            text_for_id = "<tool_result>"
            turn_id = Turn.make_turn_id(session_id, ordinal, text_for_id)
            te.parent_turn_id = turn_id
            turn = Turn(
                turn_id=turn_id,
                session_id=session_id,
                ordinal=ordinal,
                role="tool",
                content=[
                    ContentBlock(
                        kind="tool_result",
                        output=output,
                        tool_use_id=call_id,
                        is_error=False,
                    )
                ],
                tool_events=[te],
                ts_utc=ts,
                model=None,
                cli="codex",
                worktree_id=worktree_id,
                parent_branch=parent_branch,
                parent_turn_id=last_turn_id,
            )
            turn._raw_records = [r]
            turns.append(turn)
            last_turn_id = turn_id
            ordinal += 1
        elif ptype == "reasoning":
            # Codex encrypts reasoning content; we keep an opaque placeholder
            text_for_id = f"<reasoning:{payload.get('summary', '')!r}>"
            turn_id = Turn.make_turn_id(session_id, ordinal, text_for_id)
            turn = Turn(
                turn_id=turn_id,
                session_id=session_id,
                ordinal=ordinal,
                role="assistant",
                content=[
                    ContentBlock(
                        kind="thinking",
                        text="[encrypted reasoning, see _raw_records]",
                    )
                ],
                tool_events=[],
                ts_utc=ts,
                model=None,
                cli="codex",
                worktree_id=worktree_id,
                parent_branch=parent_branch,
                parent_turn_id=last_turn_id,
            )
            turn._raw_records = [r]
            turns.append(turn)
            last_turn_id = turn_id
            ordinal += 1
        else:
            # Unknown payload type — preserve as system turn
            text_for_id = f"<{ptype}>"
            turn_id = Turn.make_turn_id(session_id, ordinal, text_for_id)
            turn = Turn(
                turn_id=turn_id,
                session_id=session_id,
                ordinal=ordinal,
                role="system",
                content=[ContentBlock(kind="other", text=json.dumps(payload)[:1000])],
                tool_events=[],
                ts_utc=ts,
                model=None,
                cli="codex",
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
        cli="codex",
        source_path=str(p.resolve()),
        project_dir=str(p.parent),
        cwd=cwd,
        worktree_id=worktree_id,
        parent_branch=parent_branch,
        started_utc=started_utc,
        ended_utc=ended_utc,
        turns=turns,
        base_instructions=base_instructions,
        cli_version=cli_version,
        model_provider=model_provider or "openai",
        metadata={
            "n_raw_records": len(raw_records),
            "originator": originator,
            "forked_from_id": forked_from_id,
            "agent_nickname": agent_nickname,
            "extra_session_metas_count": len(extra_session_metas),
        },
    )
    session._raw_records = raw_records
    return session


def iter_codex_sessions(
    sessions_root: str | Path = "/Users/aiSandbox/.codex/sessions",
    archived_root: str | Path = "/Users/aiSandbox/.codex/archived_sessions",
    require_cwd_contains: Optional[str] = "roomd",
) -> Iterator[Path]:
    """Yield Codex rollout JSONL paths, optionally filtered by cwd substring."""
    roots = [Path(sessions_root), Path(archived_root)]
    for root in roots:
        if not root.exists():
            continue
        for jsonl in sorted(root.rglob("*.jsonl")):
            if jsonl.stat().st_size == 0:
                continue
            if require_cwd_contains is None:
                yield jsonl
            else:
                # Cheap check: scan only first record (session_meta) for cwd
                try:
                    with jsonl.open("r") as f:
                        first = f.readline()
                    if not first:
                        continue
                    d = json.loads(first)
                    payload = d.get("payload") or {}
                    if require_cwd_contains in str(payload.get("cwd", "")):
                        yield jsonl
                except Exception:
                    continue
