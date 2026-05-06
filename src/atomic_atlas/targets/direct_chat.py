"""DirectChatTarget — drive a direct chat against any OpenAI-compatible endpoint.

Closes the gap where ``direct_chat`` raised ``UnsupportedVectorError`` and
forced users into the agent runner for chat-only atomics. Wraps PyRIT's
``OpenAIChatTarget`` so atomic-atlas does not re-implement chat plumbing —
PyRIT handles request construction, retries, and response parsing; we just
configure it from the target profile.

Profile shape:

    adapters:
      direct_chat:
        type: openai_compatible
        api_key: ${VAR}        # or auth: {type: bearer, token: ${VAR}}
        model: <deployment-or-model-name>
        # endpoint: optional override; defaults to {base_url}/v1/chat/completions

Works against any OpenAI-compatible endpoint: DVAA HelperBot/LegacyBot/etc.,
production Azure OpenAI agents, LiteLLM proxies, vLLM, Ollama-OpenAI shim.
"""

from __future__ import annotations

from typing import Any

from .base import AtomicAtlasTarget
from ..parser import AtomicTest


class DirectChatTarget(AtomicAtlasTarget):
    """Delivers a direct chat turn against an OpenAI-compatible chat endpoint.

    setup() and cleanup() are no-ops (chat is stateless from the target's
    perspective). send_prompt_async() delegates to a wrapped PyRIT
    OpenAIChatTarget configured from the profile.
    """

    def __init__(self, atomic: AtomicTest, target_profile: dict[str, Any]) -> None:
        super().__init__(atomic, target_profile)

        # PyRIT's OpenAI SDK appends the chat-completions path itself; pass
        # the base URL without /chat/completions to avoid the SDK warning.
        # We accept both shapes in the profile (with or without /v1) and
        # normalize to the form the SDK expects.
        base_url = target_profile.get("base_url", "").rstrip("/")
        endpoint = self._adapter_config.get("endpoint", "").rstrip("/")
        if not endpoint:
            endpoint = base_url
        # Strip the chat-completions suffix if a user accidentally included
        # it; PyRIT's OpenAI SDK adds it itself. Leave the /v1 prefix alone —
        # routing on most OpenAI-compatible servers (DVAA included) needs it.
        if endpoint.endswith("/chat/completions"):
            endpoint = endpoint[: -len("/chat/completions")]

        api_key = self._adapter_config.get("api_key", "")
        if api_key:
            api_key = self._resolve_env(api_key)
        else:
            # Fall back to bearer token in adapter auth block.
            auth = self._adapter_config.get("auth", {})
            if auth.get("type") == "bearer" and auth.get("token"):
                api_key = self._resolve_env(auth["token"])

        model_name = self._adapter_config.get("model", "default")

        # PyRIT import is deliberately lazy: this module must remain importable
        # without PyRIT installed (the lightweight install path).
        from pyrit.prompt_target import OpenAIChatTarget

        self._chat = OpenAIChatTarget(
            model_name=model_name,
            endpoint=endpoint,
            api_key=api_key or "unused",
        )

    async def setup(self) -> None:
        return None

    async def cleanup(self) -> None:
        return None

    async def send_prompt_async(self, *, message):
        return await self._chat.send_prompt_async(message=message)
