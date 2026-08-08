"""
llm_client.py

Thin wrapper around the Anthropic API. Reads ANTHROPIC_API_KEY from the
environment. If no key is set, falls back to a deterministic template
response so the rest of the pipeline (retrieval, eval harness, reporting)
can still be demoed end-to-end without live credentials.

The fallback is NOT trying to fake an LLM. It's there so `run_demo.py`
and `run_eval.py` are runnable by anyone who clones the repo, with the
real model swapped in the moment a key is exported. Set the env var to
see the actual agent reasoning.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

_MODEL = "claude-sonnet-4-5"


@dataclass
class LLMResponse:
    text: str
    model: str
    latency_s: float
    live: bool  # True if this came from the real API, False if fallback


def _fallback_response(prompt: str) -> str:
    """Deterministic, clearly-labeled stand-in. Does not claim to be a model output."""
    return (
        "[OFFLINE FALLBACK — no ANTHROPIC_API_KEY set, real model was not called]\n"
        "Based on the retrieved policy context only: this transaction matches the "
        "pattern described in the retrieved policy chunk(s) above. Set "
        "ANTHROPIC_API_KEY to get a real grounded explanation from the model."
    )


def call_llm(prompt: str, system: str | None = None, max_tokens: int = 400) -> LLMResponse:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    start = time.time()

    if not api_key:
        return LLMResponse(
            text=_fallback_response(prompt),
            model="offline-fallback",
            latency_s=time.time() - start,
            live=False,
        )

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    kwargs = {}
    if system:
        kwargs["system"] = system
    response = client.messages.create(
        model=_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return LLMResponse(
        text=text,
        model=_MODEL,
        latency_s=time.time() - start,
        live=True,
    )
