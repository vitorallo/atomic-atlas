"""MCPServerTarget — register a poisoned tool on an MCP server, then trigger discovery."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .base import AtomicAtlasTarget
from ..parser import AtomicTest

logger = logging.getLogger(__name__)


class MCPServerTarget(AtomicAtlasTarget):
    """
    Delivers prompt injection or data exfiltration via a malicious MCP tool registration.

    Supported modes (set in target profile adapter config):
      - http_registry_stub : POST to an HTTP MCP tool registry endpoint.
        This is a v0.1 placeholder — there is no standard for registering tools
        with an MCP server over HTTP today. The agent runner (Claude Code skill
        / MCP server) handles real MCP targets by reasoning about the specific
        target's tool registration mechanism. See PRD open question #4.
      - mcp_jsonrpc : Real MCP JSON-RPC 2.0 over HTTP. POSTs tools/list,
        tools/call (and optionally tools/register / tools/unregister) to a
        single endpoint root. Compatible with servers like DVAA's ToolBot.
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
        self._baseline_tools: list[dict[str, Any]] = []
        self._jsonrpc_id = 0

    async def setup(self) -> None:
        mode = self._adapter_config.get("type", "http_registry_stub")
        if mode == "http_registry_stub":
            await self._register_http()
        elif mode == "mcp_jsonrpc":
            await self._setup_jsonrpc()
        else:
            raise NotImplementedError(f"MCPServerTarget: unsupported mode '{mode}'")

    async def cleanup(self) -> None:
        mode = self._adapter_config.get("type", "http_registry_stub")
        if mode == "mcp_jsonrpc":
            await self._cleanup_jsonrpc()
            return
        if not self._registered_tool_id:
            return
        if mode == "http_registry_stub":
            await self._deregister_http()

    async def send_prompt_async(self, *, message):
        mode = self._adapter_config.get("type", "http_registry_stub")
        if mode == "mcp_jsonrpc":
            return await self._send_jsonrpc(message=message)
        from pyrit.models import construct_response_from_request
        request_piece = message.message_pieces[0]
        user_text = request_piece.converted_value
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        body = {
            "model": self._adapter_config.get("model", "default"),
            "messages": [{"role": "user", "content": user_text}],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._chat_url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        reply = data["choices"][0]["message"]["content"]
        return [construct_response_from_request(request=request_piece, response_text_pieces=[reply])]

    # --- mcp_jsonrpc: real MCP JSON-RPC 2.0 over HTTP ---

    async def _jsonrpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        base = self._resolve_env(self._adapter_config.get("base_url", ""))
        if not base:
            raise ValueError("MCPServerTarget mcp_jsonrpc: 'base_url' not set in adapter config")
        self._jsonrpc_id += 1
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": self._jsonrpc_id}
        if params is not None:
            body["params"] = params
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(base.rstrip("/") + "/", json=body, headers=headers)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def _supports_method(tools: list[dict[str, Any]], method: str) -> bool:
        # Servers may advertise non-standard methods (tools/register, tools/unregister)
        # as capability markers in tools/list — match either by name or by a methods/
        # capabilities list on the marker entry.
        for t in tools:
            if t.get("name") == method:
                return True
            methods = t.get("methods") or t.get("capabilities") or []
            if isinstance(methods, list) and method in methods:
                return True
        return False

    async def _setup_jsonrpc(self) -> None:
        list_resp = await self._jsonrpc("tools/list")
        result = list_resp.get("result") or {}
        tools = result.get("tools", result) if isinstance(result, dict) else result
        self._baseline_tools = tools if isinstance(tools, list) else []

        register_tool = self._adapter_config.get("register_tool")
        if register_tool and self._supports_method(self._baseline_tools, "tools/register"):
            reg = (await self._jsonrpc("tools/register", register_tool)).get("result") or {}
            self._registered_tool_id = reg.get("id") or reg.get("name") or register_tool.get("name")

    async def _send_jsonrpc(self, *, message):
        from pyrit.models import construct_response_from_request
        request_piece = message.message_pieces[0]
        target_tool = self._adapter_config.get("target_tool")
        if not target_tool:
            raise ValueError("MCPServerTarget mcp_jsonrpc: 'target_tool' not set in adapter config")
        data = await self._jsonrpc(
            "tools/call",
            {"name": target_tool, "arguments": self._adapter_config.get("tool_arguments", {})},
        )
        if data.get("error"):
            return [construct_response_from_request(
                request=request_piece,
                response_text_pieces=[data["error"].get("message", "JSON-RPC error")],
                error="processing",
            )]
        result = data.get("result")
        if isinstance(result, dict) and isinstance(result.get("content"), list):
            text = "".join(
                item.get("text", "") for item in result["content"]
                if isinstance(item, dict) and item.get("type") == "text"
            )
        elif isinstance(result, dict) and isinstance(result.get("content"), str):
            text = result["content"]
        else:
            text = "" if result is None else json.dumps(result)
        return [construct_response_from_request(request=request_piece, response_text_pieces=[text])]

    async def _cleanup_jsonrpc(self) -> None:
        if not self._registered_tool_id:
            return
        if not self._supports_method(self._baseline_tools, "tools/unregister"):
            logger.warning(
                "MCPServerTarget mcp_jsonrpc: server lacks tools/unregister; "
                "leaving %s registered", self._registered_tool_id,
            )
            return
        try:
            await self._jsonrpc("tools/unregister", {"id": self._registered_tool_id})
        except Exception as exc:  # pragma: no cover — best-effort cleanup
            logger.warning("tools/unregister failed: %s", exc)

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
