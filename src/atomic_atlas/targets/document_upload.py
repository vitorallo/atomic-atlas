"""DocumentUploadTarget — submit a payload document to an agent's file ingestion endpoint."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from .base import AtomicAtlasTarget
from ..parser import AtomicTest


class DocumentUploadTarget(AtomicAtlasTarget):
    """
    Delivers indirect prompt injection by uploading a poisoned document.

    Unlike RAGCorpusTarget, this does not require persistent write access to the
    RAG index — the attacker is the user submitting the file. The document is
    uploaded via the agent's file/attachment endpoint, then a trigger message
    asks the agent to process it.
    """

    def __init__(
        self,
        atomic: AtomicTest,
        target_profile: dict[str, Any],
        payload_path: Path,
    ) -> None:
        super().__init__(atomic, target_profile)
        self.payload_path = payload_path
        self._uploaded_file_id: str | None = None
        self._upload_url = target_profile.get("base_url", "").rstrip("/") + "/v1/files"
        self._chat_url = target_profile.get("base_url", "").rstrip("/") + "/v1/chat/completions"

    async def setup(self) -> None:
        upload_url = self._adapter_config.get("upload_url") or self._upload_url
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=30) as client:
            with self.payload_path.open("rb") as f:
                resp = await client.post(
                    upload_url,
                    headers=headers,
                    files={"file": (self.payload_path.name, f, "text/plain")},
                    data={"purpose": "assistants"},
                )
                resp.raise_for_status()
                data = resp.json()
                self._uploaded_file_id = data.get("id") or data.get("file_id")

    async def cleanup(self) -> None:
        if not self._uploaded_file_id:
            return
        delete_url = self._adapter_config.get("delete_url") or (
            self._upload_url + f"/{self._uploaded_file_id}"
        )
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=15) as client:
            await client.delete(delete_url, headers=headers)

    async def send_prompt_async(self, *, prompt_request):
        from pyrit.models import construct_response_from_request
        message = prompt_request.request_pieces[0].converted_value
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        attachments = (
            [{"file_id": self._uploaded_file_id, "tools": [{"type": "file_search"}]}]
            if self._uploaded_file_id
            else []
        )
        body = {
            "model": self._adapter_config.get("model", "default"),
            "messages": [{"role": "user", "content": message}],
            "attachments": attachments,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._chat_url, json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        reply = data["choices"][0]["message"]["content"]
        return construct_response_from_request(request=prompt_request, response_text_pieces=[reply])
