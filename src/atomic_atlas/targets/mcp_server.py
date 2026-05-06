"""MCPServerTarget — register a poisoned tool on an MCP server, then trigger discovery."""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import AtomicAtlasTarget
from ..parser import AtomicTest


class MCPServerTarget(AtomicAtlasTarget):
    """
    Delivers prompt injection or data exfiltration via a malicious MCP tool registration.

    Supported modes (set in target profile adapter config):
      - http_registry_stub : POST to an HTTP MCP tool registry endpoint.
        This is a v0.1 placeholder — there is no standard for registering tools
        with an MCP server over HTTP today. The agent runner (Claude Code skill
        / MCP server) handles real MCP targets by reasoning about the specific
        target's tool registration mechanism. See PRD open question #4.
      - rogue_server : Start a rogue MCP server that the agent connects to (v0.2).

    setup() registers the poisoned tool.
    send_prompt_async() sends the trigger message to the agent chat interface.
    cleanup() deregisters the tool.
    """

    def __init__(
        self,
        atomic: AtomicTest,
        target_profile: dict[str, Any],
        tool_payload: dict[str, Any],
    ) -> None:
        super().__init__(atomic, target_profile)
        self.tool_payload = tool_payload  # the poisoned tool definition (name, description, schema)
        self._registered_tool_id: str | None = None
        self._chat_url = target_profile.get("base_url", "").rstrip("/") + "/v1/chat/completions"

    async def setup(self) -> None:
        mode = self._adapter_config.get("type", "http_registry_stub")
        if mode == "http_registry_stub":
            await self._register_http()
        else:
            raise NotImplementedError(f"MCPServerTarget: unsupported mode '{mode}'")

    async def cleanup(self) -> None:
        if not self._registered_tool_id:
            return
        mode = self._adapter_config.get("type", "http_registry_stub")
        if mode == "http_registry_stub":
            await self._deregister_http()

    async def send_prompt_async(self, *, prompt_request):
        from pyrit.models import construct_response_from_request
        message = prompt_request.request_pieces[0].converted_value
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        body = {
            "model": self._adapter_config.get("model", "default"),
            "messages": [{"role": "user", "content": message}],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._chat_url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        reply = data["choices"][0]["message"]["content"]
        return construct_response_from_request(request=prompt_request, response_text_pieces=[reply])

    async def _register_http(self) -> None:
        registry_url = self._resolve_env(self._adapter_config.get("registry_url", ""))
        if not registry_url:
            raise ValueError("MCPServerTarget: 'registry_url' not set in adapter config")
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(registry_url, json=self.tool_payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            self._registered_tool_id = data.get("id") or self.tool_payload.get("name")

    async def _deregister_http(self) -> None:
        registry_url = self._resolve_env(self._adapter_config.get("registry_url", ""))
        if not registry_url or not self._registered_tool_id:
            return
        deregister_url = f"{registry_url}/{self._registered_tool_id}"
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=15) as client:
            await client.delete(deregister_url, headers=headers)
