"""Smoke tests for the recon module — verify HTTP probing logic against a
mocked transport, no real network required."""

from __future__ import annotations

import json

import httpx
import pytest

from atomic_atlas.recon import recon


def _make_handler(routes: dict[tuple[str, str], tuple[int, dict | str]]):
    """Build an httpx mock handler from a {(method, path): (status, body)} map.

    Any unmatched request returns 404.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key in routes:
            status, body = routes[key]
            if isinstance(body, dict):
                return httpx.Response(status, json=body)
            return httpx.Response(status, text=body)
        return httpx.Response(404, text="not found")

    return handler


@pytest.mark.asyncio
async def test_recon_detects_chat_and_tools(monkeypatch):
    """When the target exposes chat completions and a tools schema, recon
    should detect direct_chat and tool_response, and suggest at least
    AML.T0051.001."""

    routes = {
        ("POST", "/v1/chat/completions"): (
            200,
            {"choices": [{"message": {"content": "ok"}}]},
        ),
        ("GET", "/openapi.json"): (
            200,
            {"tools": [{"name": "send_email"}, {"name": "fetch_url"}]},
        ),
    }
    transport = httpx.MockTransport(_make_handler(routes))

    # Patch httpx.AsyncClient to use our mock transport.
    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_async_client(*a, **{**kw, "transport": transport}),
    )

    result = await recon("http://target.local")

    assert "direct_chat" in result.vectors_detected
    assert "tool_response" in result.vectors_detected
    assert "send_email" in result.tools_exposed
    assert any(t.startswith("AML.T") for t in result.suggested_techniques)


@pytest.mark.asyncio
async def test_recon_detects_real_mcp_jsonrpc(monkeypatch):
    """A target that speaks real MCP JSON-RPC 2.0 at / (DVAA's ToolBot, DVMCP,
    appsecco MCP lab) must be detected as mcp_server, and its tool names
    captured. The earlier /.well-known/mcp probe alone missed these."""

    routes = {
        ("POST", "/"): (200, {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {"name": "read_file", "description": "Read a file"},
                    {"name": "execute", "description": "Execute a command"},
                ],
            },
        }),
    }
    transport = httpx.MockTransport(_make_handler(routes))

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_async_client(*a, **{**kw, "transport": transport}),
    )

    result = await recon("http://target.local")

    assert "mcp_server" in result.vectors_detected
    assert "mcp_server" not in result.vectors_unknown
    assert "read_file" in result.tools_exposed
    assert "execute" in result.tools_exposed


@pytest.mark.asyncio
async def test_recon_webhook_strict_post_only(monkeypatch):
    """Webhook detection must require a 2xx response to a benign JSON POST.
    A 404 (DVAA's behavior on /inbound) must NOT count as detected.
    Regression test for the pre-fix false positive."""

    routes = {
        # All webhook paths return 404 — like DVAA does.
        ("POST", "/webhook"): (404, "not found"),
        ("POST", "/hooks"): (404, "not found"),
        ("POST", "/inbound"): (404, "not found"),
        ("POST", "/events"): (404, "not found"),
    }
    transport = httpx.MockTransport(_make_handler(routes))

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_async_client(*a, **{**kw, "transport": transport}),
    )

    result = await recon("http://target.local")
    assert "webhook" not in result.vectors_detected, (
        "404 on webhook paths must not count as detected"
    )


@pytest.mark.asyncio
async def test_recon_webhook_detected_on_2xx(monkeypatch):
    """When a webhook handler accepts the POST and returns 2xx, it counts."""

    routes = {
        ("POST", "/inbound"): (202, {"accepted": True}),
    }
    transport = httpx.MockTransport(_make_handler(routes))

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_async_client(*a, **{**kw, "transport": transport}),
    )

    result = await recon("http://target.local")
    assert "webhook" in result.vectors_detected


@pytest.mark.asyncio
async def test_recon_rag_via_metadata(monkeypatch):
    """A target that advertises RAG in /info (DVAA RAGBot's shape) must be
    detected even when its chat responses are canned and don't contain
    RAG-revealing keywords."""

    routes = {
        ("GET", "/info"): (200, {
            "id": "ragbot",
            "name": "RAGBot",
            "features": {"rag": True, "vectorStore": "mock"},
            "knowledgeBase": [{"id": 1, "content": "policy"}],
        }),
        # Canned chat response with no RAG keywords — would defeat the
        # keyword-based fallback alone.
        ("POST", "/v1/chat/completions"): (200, {
            "choices": [{"message": {"content": "[RAGBot] I'm here to help!"}}]
        }),
    }
    transport = httpx.MockTransport(_make_handler(routes))

    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_async_client(*a, **{**kw, "transport": transport}),
    )

    result = await recon("http://target.local")
    assert "rag_corpus" in result.vectors_detected


@pytest.mark.asyncio
async def test_recon_returns_dataclass_with_expected_fields():
    """The ReconResult must expose the fields the MCP server depends on:
    vectors_detected, vectors_unknown, vectors_absent, tools_exposed,
    guardrails, suggested_techniques."""

    transport = httpx.MockTransport(_make_handler({}))

    import atomic_atlas.recon as recon_mod
    original = recon_mod.httpx.AsyncClient

    class _MockedClient(original):
        def __init__(self, *a, **kw):
            kw["transport"] = transport
            super().__init__(*a, **kw)

    recon_mod.httpx.AsyncClient = _MockedClient
    try:
        result = await recon("http://nothing.local")
    finally:
        recon_mod.httpx.AsyncClient = original

    # Empty target → all four fields exist as lists, guardrails as a dict.
    assert isinstance(result.vectors_detected, list)
    assert isinstance(result.vectors_unknown, list)
    assert isinstance(result.vectors_absent, list)
    assert isinstance(result.tools_exposed, list)
    assert isinstance(result.guardrails, dict)
    assert isinstance(result.suggested_techniques, list)
