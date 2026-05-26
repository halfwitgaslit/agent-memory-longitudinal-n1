---
name: roomd-memory-retrieval
description: At session start in any roomd project, retrieve top-k relevant memories from the configured agent-memory backend and inject them into context. Use when the current working directory is under ~/github/roomd or any roomd worktree.
allowed-tools: Read, Bash
---

# roomd-memory-retrieval

This skill implements the **injection** layer of the PhD-grade longitudinal
n=1 evaluation pipeline (architecture/v1.md §4.5). It is installed into a
real Claude Code session and runs once at session start.

## Behavior

1. Read the current arm (`$ROOMD_MEM_ARM`) from the environment.
2. Read the first user prompt of the session (available in the session's
   metadata before any tool call has run).
3. Call the retriever (`retriever.py`) with `--arm $ROOMD_MEM_ARM --query "<first user prompt>" --k 5`.
4. The retriever prints a markdown block of the form:

   ```
   ## Relevant prior knowledge
   - [memory_id=abc12345 score=0.82] "We use Pydantic v2 for all schemas"
   - [memory_id=...]
   ```

5. This block is then visible to Claude in the session's system context.

## Arms

The arm is chosen externally (pre-registered switchback design per
`eval/runner.py`). Recognized arms: `null`, `random`, `mem0`, `letta`,
`hindsight`, `cognee`.

## Provenance

Every retrieval is logged to `~/.roomd/mem_inject_log.jsonl` so the eval
harness can later compute hit-rate / recall metrics.

## Usage

When invoked, run:

```bash
python3 retriever.py --arm "${ROOMD_MEM_ARM:-null}" --query "$1" --k 5
```

Where `$1` is the first user prompt of the session.
