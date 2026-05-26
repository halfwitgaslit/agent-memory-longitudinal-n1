"""ClaudeCliLLM: a Mem0-compatible LLM provider that routes calls through the
local ``claude -p`` CLI instead of the Anthropic HTTP API.

This means Mem0's internal fact-extraction / summarization calls bill against
the user's Claude Code subscription rather than requiring a separate
ANTHROPIC_API_KEY. The exact pattern is documented in
``session_memory_compaction/harness_client.py``; this is the same idea adapted
to Mem0's ``LLMBase`` interface.

Registration: this module monkey-patches ``mem0.utils.factory.LlmFactory`` so
that ``provider: "claude_cli"`` becomes a recognized backend at runtime. Call
``register_claude_cli_provider()`` exactly once before any Mem0 init.

USAGE
=====
    from memory.claude_cli_llm import register_claude_cli_provider
    register_claude_cli_provider()
    # Now Mem0 config can use {"llm": {"provider": "claude_cli", "config": {"model": "claude-haiku-4-5"}}}
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


# Single shared resolver for the claude binary
def _resolve_claude_bin() -> str:
    p = os.environ.get("CLAUDE_BIN") or shutil.which("claude")
    if not p:
        raise RuntimeError(
            "Could not find 'claude' on PATH. Install Claude Code first, or set CLAUDE_BIN."
        )
    return p


def _stringify_content(content: Any) -> str:
    """Mirror harness_client._stringify_content for Mem0 message shape."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                else:
                    parts.append(json.dumps(block))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _format_prompt(system: Optional[str], messages: List[Dict]) -> str:
    """Flatten system + messages into one prompt the CLI can ingest.

    Closely mirrors session_memory_compaction/harness_client.py:_format_prompt.
    """
    out: List[str] = []
    if system:
        out.append(f"[SYSTEM]\n{system}\n")
    for msg in messages:
        role = msg.get("role", "user").upper()
        text = _stringify_content(msg.get("content", ""))
        out.append(f"[{role}]\n{text}\n")
    out.append("[ASSISTANT]\n")
    return "\n".join(out)


def _run_claude_cli(
    prompt: str,
    model: str = "claude-haiku-4-5",
    timeout: int = 180,
) -> Dict[str, Any]:
    """Shell out to ``claude -p`` and return parsed JSON.

    Raises RuntimeError on non-zero exit or unparseable output (this is
    intentional — silent failure is the bug HONEST-Mem exists to prevent).
    """
    bin_ = _resolve_claude_bin()
    cmd = [bin_, "-p", "--output-format", "json", "--model", model]
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude -p failed (rc={proc.returncode}): {proc.stderr[:500]}"
        )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Could not parse claude -p JSON output: {e}\n{proc.stdout[:500]}"
        ) from e
    return data


# Module-level metering so we can audit total spend per process
_TOTAL_USD = 0.0
_TOTAL_CALLS = 0
_TOTAL_INPUT_TOKENS = 0
_TOTAL_OUTPUT_TOKENS = 0


def get_claude_cli_meter() -> Dict[str, Any]:
    return {
        "total_calls": _TOTAL_CALLS,
        "total_usd": round(_TOTAL_USD, 4),
        "total_input_tokens": _TOTAL_INPUT_TOKENS,
        "total_output_tokens": _TOTAL_OUTPUT_TOKENS,
    }


def reset_claude_cli_meter() -> None:
    global _TOTAL_USD, _TOTAL_CALLS, _TOTAL_INPUT_TOKENS, _TOTAL_OUTPUT_TOKENS
    _TOTAL_USD = 0.0
    _TOTAL_CALLS = 0
    _TOTAL_INPUT_TOKENS = 0
    _TOTAL_OUTPUT_TOKENS = 0


# Lazy imports: only pull in mem0 internals when actually registering.
def register_claude_cli_provider() -> None:
    """Monkey-patch mem0's LlmFactory to recognize 'claude_cli' provider.

    Idempotent: calling more than once is a no-op.
    """
    try:
        from mem0.utils.factory import LlmFactory
        from mem0.llms.base import LLMBase
        from mem0.configs.llms.base import BaseLlmConfig
    except ImportError as e:
        raise RuntimeError(f"mem0 not installed; cannot register claude_cli LLM: {e}")

    if "claude_cli" in LlmFactory.provider_to_class:
        return  # already registered

    # ALSO patch mem0's LlmConfig validator (it has its own hard-coded
    # provider allowlist that rejects unknowns before LlmFactory is consulted).
    #
    # Pydantic v2 stores the validator function in the model's
    # __pydantic_decorators__ table. We replace the function while keeping
    # all other validation logic intact — much less brittle than subclassing
    # and re-registering MemoryConfig.
    # Direct approach: replace the bound classmethod's underlying function.
    # The original Pydantic decorator wraps a classmethod-style validator;
    # we monkey-patch the original LlmConfig's class attribute so that the
    # already-registered decorator picks up the patched function.
    try:
        from mem0.llms import configs as _mem0_llm_configs

        LlmConfig = _mem0_llm_configs.LlmConfig
        # Find the validator function and patch its underlying __func__
        # (Pydantic v2 stores it as classmethod).
        decorators = LlmConfig.__pydantic_decorators__
        for name, dec in list(decorators.field_validators.items()):
            if "config" not in dec.info.fields:
                continue
            original = dec.func

            # Pydantic stores validators as bound classmethods. The bound
            # callable's signature is (v, values) — `cls` is auto-bound.
            # We mimic that exact shape with a bound-style closure.
            if hasattr(original, "__func__"):
                # bound classmethod: introspect the underlying function
                orig_class = original.__self__
                orig_func = original.__func__
            else:
                orig_class = LlmConfig
                orig_func = original

            def _make(klass, orig_fn):
                def _patched(v, values):
                    provider = values.data.get("provider")
                    if provider == "claude_cli":
                        return v
                    return orig_fn(klass, v, values)
                _patched.__name__ = orig_fn.__name__
                _patched.__qualname__ = orig_fn.__qualname__
                # Mimic bound classmethod
                _patched.__self__ = klass  # type: ignore[attr-defined]
                return _patched
            dec.func = _make(orig_class, orig_func)
        LlmConfig.model_rebuild(force=True)
        try:
            from mem0.configs.base import MemoryConfig  # type: ignore
            MemoryConfig.model_rebuild(force=True)
        except Exception:
            pass
    except Exception as patch_e:
        logger.warning("Could not patch mem0 LlmConfig validator: %s", patch_e)

    class ClaudeCliLLM(LLMBase):  # type: ignore[misc]
        """Mem0 LLM provider routing through the local ``claude -p`` CLI."""

        def __init__(self, config: Optional[Union[BaseLlmConfig, Dict]] = None):
            if config is None:
                config = BaseLlmConfig(model="claude-haiku-4-5")
            elif isinstance(config, dict):
                config = BaseLlmConfig(**config)
            super().__init__(config)
            if not self.config.model:
                self.config.model = "claude-haiku-4-5"
            # Surface a clear error early if the binary is missing
            _resolve_claude_bin()

        def generate_response(  # type: ignore[override]
            self,
            messages: List[Dict[str, str]],
            response_format: Any = None,
            tools: Any = None,
            tool_choice: str = "auto",
            **kwargs: Any,
        ) -> str:
            # Separate system message (mirrors Mem0's Anthropic provider behavior)
            system_message = ""
            filtered: List[Dict[str, str]] = []
            for m in messages:
                if m.get("role") == "system":
                    system_message = _stringify_content(m.get("content", ""))
                else:
                    filtered.append(
                        {"role": m.get("role", "user"), "content": _stringify_content(m.get("content", ""))}
                    )
            # response_format support: mem0 often passes type='json_object'
            need_json = False
            if isinstance(response_format, dict):
                if response_format.get("type") in ("json_object", "json"):
                    need_json = True
            if need_json:
                if system_message:
                    system_message += (
                        "\n\nIMPORTANT: Output ONLY valid JSON. No code fences. "
                        "No prose. Just a single JSON object."
                    )
                else:
                    system_message = (
                        "Output ONLY valid JSON. No code fences. No prose. "
                        "Just a single JSON object."
                    )
            prompt = _format_prompt(system_message, filtered)
            t0 = time.time()
            data = _run_claude_cli(prompt, model=self.config.model)
            elapsed_ms = int((time.time() - t0) * 1000)

            text = data.get("result", "") or ""
            # Strip code fences if Claude wrapped JSON despite instruction
            if need_json:
                text = _strip_code_fences(text)

            usage = data.get("usage") or {}
            cost = float(data.get("total_cost_usd") or 0.0)

            global _TOTAL_USD, _TOTAL_CALLS, _TOTAL_INPUT_TOKENS, _TOTAL_OUTPUT_TOKENS
            _TOTAL_CALLS += 1
            _TOTAL_USD += cost
            _TOTAL_INPUT_TOKENS += int(usage.get("input_tokens") or 0)
            _TOTAL_OUTPUT_TOKENS += int(usage.get("output_tokens") or 0)

            logger.info(
                "claude_cli call: %dms, $%.4f, in=%d out=%d total_usd_so_far=$%.4f",
                elapsed_ms, cost, _TOTAL_INPUT_TOKENS, _TOTAL_OUTPUT_TOKENS, _TOTAL_USD,
            )
            return text

    # Register provider
    LlmFactory.provider_to_class["claude_cli"] = (
        "memory.claude_cli_llm.ClaudeCliLLM",
        BaseLlmConfig,
    )
    # Also patch the class into this module namespace so factory's importlib resolves
    globals()["ClaudeCliLLM"] = ClaudeCliLLM


def _strip_code_fences(text: str) -> str:
    """Strip ```json ... ``` fences if the CLI wrapped its output despite instruction."""
    t = text.strip()
    if t.startswith("```"):
        # remove opening fence
        first_nl = t.find("\n")
        if first_nl != -1:
            t = t[first_nl + 1 :]
        # remove closing fence
        if t.endswith("```"):
            t = t[: -3]
    return t.strip()
