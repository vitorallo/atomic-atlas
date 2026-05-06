"""ToolResponseTarget — serve a poisoned tool response from a mock HTTP server."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import httpx

from .base import AtomicAtlasTarget
from ..parser import AtomicTest


class ToolResponseTarget(AtomicAtlasTarget):
    """
    Delivers indirect prompt injection by acting as a mock tool server.

    The target agent must be configured to call a tool whose endpoint points at
    the mock server's address (documented in the atomic's Prerequisites section).

    setup() starts the mock server.
    send_prompt_async() triggers the agent interaction that causes it to call the tool.
    cleanup() stops the mock server and restores the original tool configuration.
    """

    def __init__(
        self,
        atomic: AtomicTest,
        target_profile: dict[str, Any],
        poisoned_response: dict[str, Any],
    ) -> None:
        super().__init__(atomic, target_profile)
        self.poisoned_response = poisoned_response
        self._server: HTTPServer | None = None
        self._server_thread: threading.Thread | None = None
        self._chat_url = target_profile.get("base_url", "").rstrip("/") + "/v1/chat/completions"
        self._mock_port = self._adapter_config.get("port", 9090)

    async def setup(self) -> None:
        poisoned = self.poisoned_response

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(poisoned).encode())

            def do_POST(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(poisoned).encode())

            def log_message(self, *args):
                pass  # silence default logging

        self._server = HTTPServer(("localhost", self._mock_port), Handler)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()

    async def cleanup(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None

    async def send_prompt_async(self, *, message):
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
