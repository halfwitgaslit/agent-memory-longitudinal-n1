#!/usr/bin/env bash
# Codex memory-injection wrapper.
#
# Usage:
#   inject.sh "<first user prompt>"
#
# Writes an AGENTS.md.roomd-mem file in the cwd with the retrieved memory
# block, and then prints a message instructing how to invoke codex.
#
# Env vars consulted:
#   ROOMD_MEM_ARM   : one of {null, random, mem0, letta, hindsight, cognee}
#   ROOMD_WORKTREE  : the current worktree id (free-form)
#   ROOMD_BRANCH    : the current branch
#   PHD_PY          : full path to the phd venv python (default: /opt/homebrew/bin/python3)
#   PHD_CODE_DIR    : full path to phd/code (default: derived)

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 \"<first user prompt>\"" >&2
  exit 2
fi

FIRST_PROMPT="$1"
ROOMD_MEM_ARM="${ROOMD_MEM_ARM:-null}"
PHD_PY="${PHD_PY:-/opt/homebrew/bin/python3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PHD_CODE_DIR="${PHD_CODE_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
RETRIEVER="$PHD_CODE_DIR/injection/claude_code_skill/retriever.py"

if [ ! -f "$RETRIEVER" ]; then
  echo "[inject.sh] retriever not found at $RETRIEVER" >&2
  exit 3
fi

MEM_BLOCK=$("$PHD_PY" "$RETRIEVER" \
  --arm "$ROOMD_MEM_ARM" \
  --query "$FIRST_PROMPT" \
  --k 5 2>/dev/null || true)

if [ -n "$MEM_BLOCK" ]; then
  printf "%s\n" "$MEM_BLOCK" > ./AGENTS.md.roomd-mem
  echo "[inject.sh] Wrote $(pwd)/AGENTS.md.roomd-mem (arm=$ROOMD_MEM_ARM)" >&2
else
  echo "[inject.sh] No memory block produced (arm=$ROOMD_MEM_ARM)" >&2
fi
