"""Single source of truth for outbound LLM calls.

Three call sites used to build their own client:

- ``runner._default_red_team_chat`` (PyRIT attacker LLM for RedTeamingAttack)
- ``scorers.LLMJudgeScorer`` (PyRIT chat target for SelfAskTrueFalseScorer)
- ``payload_adapter._DefaultOpenAIClient`` (raw openai SDK for the adapter)

They share the same env-var convention but had drifted apart in subtle ways
(env-var override hacks for the judge model, redundant placeholder-key
checks). This module exposes one factory each call site uses.

Configuration (CLI flag > env > default):

- model:    ``ATOMIC_ATLAS_LLM_MODEL`` (default ``gpt-4o``).
- endpoint: ``OPENAI_API_BASE`` (default ``https://api.openai.com/v1``).
- key:      ``OPENAI_API_KEY``.
- offline:  ``ATOMIC_ATLAS_OFFLINE=1`` disables every LLM call site.

The legacy vars ``ATOMIC_ATLAS_ATTACKER_MODEL`` and
``ATOMIC_ATLAS_ADAPTER_MODEL`` are still honored as fallbacks for
``ATOMIC_ATLAS_LLM_MODEL`` so existing operator setups don't break, but
they're no longer documented in the public CLI reference.
"""

from __future__ import annotations

import os
from typing import Any, Optional


_PLACEHOLDER_API_KEYS = frozenset({"unused", "none", "null"})
_DEFAULT_MODEL = "gpt-4o"
_DEFAULT_ENDPOINT = "https://api.openai.com/v1"


def is_offline() -> bool:
    """True when LLM call sites should refuse to make real calls.

    Operators set ``ATOMIC_ATLAS_OFFLINE=1`` for deterministic / no-network
    runs. When true, ``runner._build_attack`` falls back from
    ``RedTeamingAttack`` to ``PromptSendingAttack`` and the scoring tier
    auto-selection skips the judge.
    """
    return os.environ.get("ATOMIC_ATLAS_OFFLINE") == "1"


def has_api_key() -> bool:
    """True when an LLM call would have a real (non-placeholder) key.

    This is the gate the runner's tier-selection / attacker-LLM branches
    use to decide whether to attempt the LLM path. Returns False if
    ``ATOMIC_ATLAS_OFFLINE=1`` is set.
    """
    if is_offline():
        return False
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        return False
    return key.lower() not in _PLACEHOLDER_API_KEYS


def resolve_model(override: Optional[str] = None) -> str:
    """Pick the LLM model name with proper precedence.

    Precedence: explicit override > ``ATOMIC_ATLAS_LLM_MODEL`` env >
    legacy ``ATOMIC_ATLAS_ATTACKER_MODEL`` env > legacy
    ``ATOMIC_ATLAS_ADAPTER_MODEL`` env > default ``gpt-4o``.
    """
    return (
        override
        or os.environ.get("ATOMIC_ATLAS_LLM_MODEL")
        or os.environ.get("ATOMIC_ATLAS_ATTACKER_MODEL")
        or os.environ.get("ATOMIC_ATLAS_ADAPTER_MODEL")
        or _DEFAULT_MODEL
    )


def chat_target(model: Optional[str] = None) -> Any:
    """Build a PyRIT ``OpenAIChatTarget`` for the attacker LLM / judge.

    Used by ``runner._build_attack`` and ``scorers.LLMJudgeScorer``. The
    returned target is constructed even when no key is set — callers that
    need the strict gate should pre-check with ``has_api_key()``.
    """
    from pyrit.prompt_target import OpenAIChatTarget
    return OpenAIChatTarget(
        model_name=resolve_model(model),
        endpoint=os.environ.get("OPENAI_API_BASE", _DEFAULT_ENDPOINT),
        api_key=os.environ.get("OPENAI_API_KEY", "unused"),
    )


async def complete(*, system: str, user: str, model: Optional[str] = None) -> str:
    """One-shot async chat completion via the openai SDK.

    Used by ``payload_adapter`` — bypasses PyRIT's Score / Memory graph
    because the adapter doesn't need it. Raises ``RuntimeError`` if no
    real API key is set; callers should check ``has_api_key()`` first
    when they want to fall back gracefully.
    """
    if not has_api_key():
        raise RuntimeError(
            "OPENAI_API_KEY missing or placeholder (or ATOMIC_ATLAS_OFFLINE=1 "
            "is set). Set a real key, or point OPENAI_API_BASE at a "
            "LiteLLM-style proxy."
        )
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )
    response = await client.chat.completions.create(
        model=resolve_model(model),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    if not response.choices or not response.choices[0].message.content:
        raise RuntimeError(
            "LLM returned an empty response — provider may have filtered "
            "the request or returned an error."
        )
    return response.choices[0].message.content
