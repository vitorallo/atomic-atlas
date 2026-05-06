"""Tests for MCPServerTarget mcp_jsonrpc mode — real MCP JSON-RPC 2.0 over HTTP.

Mocks the httpx transport so no real MCP server is required. PyRIT-required
tests are guarded with a skipif marker, matching the pattern in test_runner.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from atomic_atlas.parser import load
from atomic_atlas.targets.base import PYRIT_AVAILABLE

ATOMICS_DIR = Path(__file__).parent.parent / "atomics"
MCP_ATOMIC = ATOMICS_DIR / "AML.T0051.001/mcp_server.md"


def _make_handler(responses):
    """Build a JSON-RPC mock handler. ``responses`` is a list of dicts to
    return in order, one per POST. Unmatched/extra requests return a generic
    JSON-RPC error so the test fails loudly rather than silently."""

    state = {"i": 0, "captured": []}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content) if request.content else {}
        state["captured"].append(body)
        idx = state["i"]
        state["i"] += 1
        if idx >= len(responses):
            return httpx.Response(200, json={
                "jsonrpc": "2.0", "id": body.get("id"),
                "error": {"code": -32601, "message": "no mock response queued"},
            })
        return httpx.Response(200, json=responses[idx])

    return handler, state


def _patch_httpx(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_async_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda *a, **kw: real_async_client(*a, **{**kw, "transport": transport}),
    )


def _init_pyrit_memory() -> None:
    """Initialize PyRIT in-memory SQLite once per process. Mirrors runner._ensure_pyrit_initialized."""
    from pyrit.memory import CentralMemory, SQLiteMemory
    try:
        CentralMemory.get_memory_instance()
        return
    except (ValueError, AttributeError):
        pass
    CentralMemory.set_memory_instance(SQLiteMemory(db_path=":memory:"))


def _profile(extra: dict | None = None) -> dict:
    cfg = {
        "type": "mcp_jsonrpc",
        "base_url": "http://localhost:7010",
        "target_tool": "read_file",
        "tool_arguments": {"path": "/etc/passwd"},
    }
    if extra:
        cfg.update(extra)
    return {"base_url": "http://localhost:7010", "adapters": {"mcp_server": cfg}}


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="needs PyRIT")
@pytest.mark.asyncio
async def test_mcp_jsonrpc_setup_fetches_tools(monkeypatch):
    """setup() POSTs tools/list and stores the returned tools as the baseline."""
    from atomic_atlas.targets.mcp_server import MCPServerTarget

    handler, state = _make_handler([
        {"jsonrpc": "2.0", "id": 1, "result": {"tools": [
            {"name": "read_file", "description": "read a file"},
            {"name": "execute", "description": "shell exec"},
        ]}},
    ])
    _patch_httpx(monkeypatch, handler)

    atomic = load(MCP_ATOMIC)
    _init_pyrit_memory()
    target = MCPServerTarget(atomic, _profile(), tool_payload={})
    await target.setup()

    names = [t["name"] for t in target._baseline_tools]
    assert "read_file" in names
    assert "execute" in names
    assert state["captured"][0]["method"] == "tools/list"


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="needs PyRIT")
@pytest.mark.asyncio
async def test_mcp_jsonrpc_call_success(monkeypatch):
    """tools/call returns content[].text → joined into the response Message."""
    from pyrit.models import Message, MessagePiece
    from atomic_atlas.targets.mcp_server import MCPServerTarget

    handler, _state = _make_handler([
        {"jsonrpc": "2.0", "id": 1,
         "result": {"content": [{"type": "text", "text": "file content"}]}},
    ])
    _patch_httpx(monkeypatch, handler)

    atomic = load(MCP_ATOMIC)
    _init_pyrit_memory()
    target = MCPServerTarget(atomic, _profile(), tool_payload={})

    request = Message(message_pieces=[MessagePiece(
        role="user", original_value="please call read_file", converted_value="please call read_file",
    )])
    responses = await target.send_prompt_async(message=request)

    assert len(responses) == 1
    assert "file content" in responses[0].get_value()


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="needs PyRIT")
@pytest.mark.asyncio
async def test_mcp_jsonrpc_error_response(monkeypatch):
    """JSON-RPC error → response message carries error.message and response_error='processing'."""
    from pyrit.models import Message, MessagePiece
    from atomic_atlas.targets.mcp_server import MCPServerTarget

    handler, _state = _make_handler([
        {"jsonrpc": "2.0", "id": 1,
         "error": {"code": -32602, "message": "path not allowed"}},
    ])
    _patch_httpx(monkeypatch, handler)

    atomic = load(MCP_ATOMIC)
    _init_pyrit_memory()
    target = MCPServerTarget(atomic, _profile(), tool_payload={})

    request = Message(message_pieces=[MessagePiece(
        role="user", original_value="trigger", converted_value="trigger",
    )])
    responses = await target.send_prompt_async(message=request)

    assert "path not allowed" in responses[0].get_value()
    assert responses[0].message_pieces[0].response_error == "processing"
