"""WebhookTarget — POST a crafted payload to an agent's inbound webhook endpoint."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import httpx

from .base import AtomicAtlasTarget
from ..parser import AtomicTest


class WebhookTarget(AtomicAtlasTarget):
    """
    Delivers indirect prompt injection via a crafted inbound webhook payload.

    The attacker does not need authenticated access to the agent — only the ability
    to POST to the agent's inbound webhook endpoint (public form, unauthenticated API,
    compromised upstream system).

    setup() starts a callback listener to detect exfil.
    send_prompt_async() POSTs the crafted webhook payload to the target.
    cleanup() stops the callback listener.
    """

    def __init__(
        self,
        atomic: AtomicTest,
        target_profile: dict[str, Any],
        webhook_payload: dict[str, Any],
    ) -> None:
        super().__init__(atomic, target_profile)
        self.webhook_payload = webhook_payload
        self._webhook_url = self._adapter_config.get("webhook_url", "")
        # callback_port=0 → kernel assigns a free port; we read it back after
        # bind. Concrete port (e.g., 9091) is also supported but risks collisions
        # when multiple webhook atomics run concurrently.
        self._callback_port = self._adapter_config.get("callback_port", 0)
        self._callback_server: HTTPServer | None = None
        self._callback_thread: threading.Thread | None = None
        self._callback_received: bool = False

    async def setup(self) -> None:
        received_ref = [False]

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                received_ref[0] = True
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def do_POST(self):
                received_ref[0] = True
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *args):
                pass

        self._received_ref = received_ref
        self._callback_server = HTTPServer(("0.0.0.0", self._callback_port), CallbackHandler)
        # Read back the actual bound port (relevant when caller passed 0).
        self._callback_port = self._callback_server.server_address[1]
        self._callback_thread = threading.Thread(
            target=self._callback_server.serve_forever, daemon=True
        )
        self._callback_thread.start()

    @property
    def callback_url(self) -> str:
        """The fully-qualified callback URL the agent should be coerced to hit.

        Atomics can template ``{callback_url}`` into payloads to bind injected
        instructions to the listener that's actually running.
        """
        host = self._adapter_config.get("callback_host", "127.0.0.1")
        return f"http://{host}:{self._callback_port}/"

    async def cleanup(self) -> None:
        if self._callback_server:
            self._callback_server.shutdown()
            self._callback_server = None

    @property
    def callback_received(self) -> bool:
        return getattr(self, "_received_ref", [False])[0]

    async def send_prompt_async(self, *, message):
        from pyrit.models import construct_response_from_request
        request_piece = message.message_pieces[0]
        if not self._webhook_url:
            raise ValueError("WebhookTarget: 'webhook_url' not set in adapter config")

        headers = {"Content-Type": "application/json", **self._auth_headers()}

        # HMAC signing if configured
        hmac_secret = self._adapter_config.get("auth", {}).get("hmac_secret")
        if hmac_secret:
            body_bytes = json.dumps(self.webhook_payload).encode()
            sig = hmac.new(
                self._resolve_env(hmac_secret).encode(),
                body_bytes,
                hashlib.sha256,
            ).hexdigest()
            headers["X-Hub-Signature-256"] = f"sha256={sig}"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._webhook_url, content=body_bytes, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._webhook_url, json=self.webhook_payload, headers=headers)

        # Give the agent time to process and potentially hit the callback
        await asyncio.sleep(2)

        success_hint = "callback received" if self.callback_received else "no callback"
        return [construct_response_from_request(
            request=request_piece,
            response_text_pieces=[f"Webhook delivered (HTTP {resp.status_code}). {success_hint}."],
        )]
