# Codex prompt hook — design

Codex (OpenAI's coding CLI) consults an `AGENTS.md` file in the working
directory at session start and at compaction events. There is no native
"skill" mechanism analogous to Claude Code's `~/.claude/skills/`. To inject
memory at session start, we use a small shell wrapper that:

1. Calls the same retriever (`../claude_code_skill/retriever.py --arm $ROOMD_MEM_ARM`)
2. Writes the output into a transient `AGENTS.md.roomd-mem` file in the
   project root, OR pre-pends it to the user's first message via a
   shell-script wrapper around `codex`.

## Recommended invocation

```bash
# Wrap `codex` with memory injection
codex_with_mem() {
  local first_prompt="$1"
  local mem_block
  mem_block=$(python3 ~/.../phd/code/injection/claude_code_skill/retriever.py \
                --arm "${ROOMD_MEM_ARM:-null}" --query "$first_prompt" --k 5)
  # Stage the AGENTS.md.roomd-mem file
  echo "$mem_block" > ./AGENTS.md.roomd-mem
  # Codex will pick up AGENTS.md and friends from cwd
  codex --message "$first_prompt"
}
```

## Asymmetry caveat (documented in paper limitations)

Codex re-reads AGENTS.md only at session start and at certain compaction
boundaries — NOT on every turn. Mid-session memory updates are therefore
less responsive on Codex than on Claude Code (where the skill re-runs at
each user turn under our setup).

For Phase 2 deployment, we use the staging approach above. For Phase 3
(after we get Codex extension support), we'll explore a true session-hook
mechanism.

See `inject.sh` for a runnable wrapper.
