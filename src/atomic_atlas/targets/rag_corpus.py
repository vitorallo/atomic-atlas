"""RAGCorpusTarget — inject a payload document into a RAG index, then trigger retrieval."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any

import httpx

from .base import AtomicAtlasTarget
from ..parser import AtomicTest


class RAGCorpusTarget(AtomicAtlasTarget):
    """
    Delivers indirect prompt injection via a RAG corpus.

    Supported backend types (set in target profile adapter config):
      - chroma       : ChromaDB HTTP API
      - pinecone     : Pinecone upsert API
      - azure_search : Azure AI Search index upload
      - http_ingest  : Generic HTTP ingest endpoint (POST multipart/JSON)

    After setup(), the payload document is in the index.
    send_prompt_async() sends the trigger chat message to the agent.
    cleanup() removes the injected document.
    """

    def __init__(self, atomic: AtomicTest, target_profile: dict[str, Any], payload_path: Path) -> None:
        super().__init__(atomic, target_profile)
        self.payload_path = payload_path
        self._injected_doc_id: str | None = None
        self._chat_url = target_profile.get("base_url", "").rstrip("/") + "/v1/chat/completions"

    async def setup(self) -> None:
        backend = self._adapter_config.get("type", "http_ingest")
        payload_text = self.payload_path.read_text(encoding="utf-8")
        doc_id = "atomic-atlas-" + hashlib.sha1(payload_text.encode()).hexdigest()[:12]
        self._injected_doc_id = doc_id

        if backend == "chroma":
            await self._inject_chroma(doc_id, payload_text)
        elif backend == "azure_search":
            await self._inject_azure_search(doc_id, payload_text)
        elif backend == "http_ingest":
            await self._inject_http(doc_id, payload_text)
        else:
            raise NotImplementedError(f"RAGCorpusTarget: unsupported backend '{backend}'")

    async def cleanup(self) -> None:
        if not self._injected_doc_id:
            return
        backend = self._adapter_config.get("type", "http_ingest")
        if backend == "chroma":
            await self._delete_chroma(self._injected_doc_id)
        elif backend == "azure_search":
            await self._delete_azure_search(self._injected_doc_id)
        elif backend == "http_ingest":
            await self._delete_http(self._injected_doc_id)

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

    # --- ChromaDB ---

    async def _inject_chroma(self, doc_id: str, text: str) -> None:
        host = self._adapter_config.get("host", "localhost:8000")
        collection = self._adapter_config.get("collection", "default")
        url = f"http://{host}/api/v1/collections/{collection}/add"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, json={
                "ids": [doc_id],
                "documents": [text],
                "metadatas": [{"source": "atomic-atlas-test"}],
            })

    async def _delete_chroma(self, doc_id: str) -> None:
        host = self._adapter_config.get("host", "localhost:8000")
        collection = self._adapter_config.get("collection", "default")
        url = f"http://{host}/api/v1/collections/{collection}/delete"
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, json={"ids": [doc_id]})

    # --- Azure AI Search ---

    async def _inject_azure_search(self, doc_id: str, text: str) -> None:
        endpoint = self._resolve_env(self._adapter_config.get("endpoint", ""))
        index = self._adapter_config.get("index", "knowledge-base")
        url = f"{endpoint}/indexes/{index}/docs/index?api-version=2023-11-01"
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        body = {"value": [{"@search.action": "upload", "id": doc_id, "content": text}]}
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, json=body, headers=headers)

    async def _delete_azure_search(self, doc_id: str) -> None:
        endpoint = self._resolve_env(self._adapter_config.get("endpoint", ""))
        index = self._adapter_config.get("index", "knowledge-base")
        url = f"{endpoint}/indexes/{index}/docs/index?api-version=2023-11-01"
        headers = {"Content-Type": "application/json", **self._auth_headers()}
        body = {"value": [{"@search.action": "delete", "id": doc_id}]}
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(url, json=body, headers=headers)

    # --- Generic HTTP ingest ---

    async def _inject_http(self, doc_id: str, text: str) -> None:
        ingest_url = self._adapter_config.get("ingest_url", "")
        if not ingest_url:
            raise ValueError("RAGCorpusTarget http_ingest: 'ingest_url' not set in adapter config")
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(ingest_url, json={"id": doc_id, "content": text}, headers=headers)

    async def _delete_http(self, doc_id: str) -> None:
        delete_url = self._adapter_config.get("delete_url", "")
        if not delete_url:
            return
        headers = self._auth_headers()
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(delete_url, json={"id": doc_id}, headers=headers)
