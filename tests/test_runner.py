"""Smoke tests for the runner: vector→target mapping, UnsupportedVectorError,
PyRIT initialization, and setup-failure short-circuit."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from atomic_atlas.parser import load
from atomic_atlas.runner import (
    ADAPTER_VECTORS,
    UnsupportedVectorError,
    resolve_target,
    run_atomic,
)
from atomic_atlas.targets.base import (
    PYRIT_AVAILABLE,
    PyRITNotInstalledError,
)

ATOMICS_DIR = Path(__file__).parent.parent / "atomics"


PROFILE = {
    "base_url": "http://x",
    "adapters": {
        "rag_corpus": {"type": "http_ingest", "ingest_url": "http://x/ingest"},
        "mcp_server": {"type": "http_registry_stub", "registry_url": "http://x/mcp"},
        "tool_response": {"port": 9090},
        "document_upload": {"upload_url": "http://x/files"},
        "webhook": {"webhook_url": "http://x/inbound", "callback_port": 0},
    },
}


VECTOR_TO_CLASS = {
    "rag_corpus": "RAGCorpusTarget",
    "mcp_server": "MCPServerTarget",
    "tool_response": "ToolResponseTarget",
    "document_upload": "DocumentUploadTarget",
    "webhook": "WebhookTarget",
}


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="resolve_target needs PyRIT")
@pytest.mark.parametrize("technique_path,vector", [
    ("AML.T0051.001/rag_corpus.md", "rag_corpus"),
    ("AML.T0051.001/mcp_server.md", "mcp_server"),
    ("AML.T0053/tool_response.md", "tool_response"),
    ("AML.T0051.001/document_upload.md", "document_upload"),
    ("AML.T0093/webhook.md", "webhook"),
])
def test_resolve_target_maps_each_adapter_vector(technique_path, vector):
    atomic = load(ATOMICS_DIR / technique_path)
    target = resolve_target(atomic, PROFILE)
    assert type(target).__name__ == VECTOR_TO_CLASS[vector]
    # Cleanup any background server/listener the target created in __init__.
    # (Most targets defer setup until setup() is awaited, but ToolResponseTarget
    # and WebhookTarget can hold references that benefit from explicit drop.)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="resolve_target needs PyRIT")
def test_unsupported_vector_raises():
    """Vectors without a CLI adapter (system_prompt, web_fetch, email, etc.)
    must raise UnsupportedVectorError with an agent-runner hint. Loaded from
    a fixture .md file rather than constructed in code, per the project's
    "tests are atomic markdown files" principle.
    """
    atomic = load(FIXTURES_DIR / "adapterless_email.md")
    with pytest.raises(UnsupportedVectorError) as exc:
        resolve_target(atomic, PROFILE)
    assert "email" in str(exc.value)
    assert "agent runner" in str(exc.value).lower() or "skill" in str(exc.value).lower() or "MCP" in str(exc.value)


def test_unsupported_vector_lists_adapters():
    """The error message must enumerate the supported adapter vectors so the
    user knows which vectors do work via the CLI."""
    err = UnsupportedVectorError("email")
    msg = str(err)
    for vector in ADAPTER_VECTORS:
        assert vector in msg, f"adapter vector {vector!r} missing from error message"


@pytest.mark.skipif(PYRIT_AVAILABLE, reason="exercises the no-PyRIT branch")
def test_pyrit_not_installed_error_when_pyrit_missing():
    """When PyRIT is absent, instantiating an AtomicAtlasTarget must raise the
    typed exception with an install hint — not a generic ImportError."""
    atomic = load(ATOMICS_DIR / "AML.T0051.001/rag_corpus.md")
    with pytest.raises(PyRITNotInstalledError) as exc:
        resolve_target(atomic, PROFILE)
    assert "atomic-atlas[orchestrator]" in str(exc.value)


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="run_atomic needs PyRIT")
@pytest.mark.asyncio
async def test_run_atomic_short_circuits_on_setup_failure():
    """If target.setup() raises, run_atomic must NOT execute the run loop —
    it should record a single setup error and skip the iterations."""
    atomic = load(ATOMICS_DIR / "AML.T0051.001/rag_corpus.md")
    target = resolve_target(atomic, PROFILE)

    target.setup = AsyncMock(side_effect=RuntimeError("ingest API unreachable"))
    target.cleanup = AsyncMock()

    result = await run_atomic(atomic, target, authorized=True)

    assert result.errors == atomic.runs, "all runs should be marked errored"
    assert result.successes == 0
    assert result.failures == 0
    # Exactly one entry in run_details, tagged with phase=setup.
    assert len(result.run_details) == 1
    assert result.run_details[0]["phase"] == "setup"
    assert "ingest API unreachable" in result.run_details[0]["error"]
    # cleanup() must still run so partial state is removed.
    target.cleanup.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_atomic_requires_authorized():
    """run_atomic must refuse to run without authorized=True, regardless of
    whether PyRIT is installed."""
    atomic = load(ATOMICS_DIR / "AML.T0051.001/rag_corpus.md")
    # We don't even need a real target — the auth gate runs before target use.
    fake_target = AsyncMock()
    if PYRIT_AVAILABLE:
        with pytest.raises(PermissionError):
            await run_atomic(atomic, fake_target, authorized=False)
    else:
        # When PyRIT is missing, require_pyrit() fires first, before the auth
        # gate. Either typed exception is acceptable here — the point is that
        # run_atomic does not silently execute.
        with pytest.raises((PermissionError, PyRITNotInstalledError)):
            await run_atomic(atomic, fake_target, authorized=False)


def test_load_profile_resolves_env_substitutions(tmp_path, monkeypatch):
    """load_profile substitutes ${VAR} from the env at load time, recursively
    through dicts and lists. Missing vars stay as literal ${VAR} so the
    operator sees which credential failed at HTTP time."""
    from atomic_atlas.runner import load_profile

    monkeypatch.setenv("ATOMIC_ATLAS_TEST_KEY", "sk-resolved-12345")
    monkeypatch.delenv("ATOMIC_ATLAS_NEVER_SET", raising=False)

    profile_file = tmp_path / "profile.yaml"
    profile_file.write_text(
        "base_url: http://localhost:7003/v1\n"
        "target_context:\n"
        "  agent_role: tester\n"
        "  expected_tools:\n"
        "    - tool_with_${ATOMIC_ATLAS_TEST_KEY}\n"
        "adapters:\n"
        "  direct_chat:\n"
        "    api_key: ${ATOMIC_ATLAS_TEST_KEY}\n"
        "    fallback_token: ${ATOMIC_ATLAS_NEVER_SET}\n"
    )
    profile = load_profile(profile_file)

    assert profile["adapters"]["direct_chat"]["api_key"] == "sk-resolved-12345"
    assert (
        profile["adapters"]["direct_chat"]["fallback_token"]
        == "${ATOMIC_ATLAS_NEVER_SET}"  # stays literal — caller sees what's missing
    )
    # Nested list values resolved too
    assert profile["target_context"]["expected_tools"] == ["tool_with_sk-resolved-12345"]
    # Non-string scalars untouched
    assert profile["base_url"] == "http://localhost:7003/v1"


def test_has_api_key_external_provider_skips_placeholder_check(monkeypatch):
    """When OPENAI_API_BASE points at a non-OpenAI provider (OpenRouter,
    Ollama, vLLM, LiteLLM), placeholder/empty keys are accepted — the
    upstream provider gates auth itself."""
    from atomic_atlas.llm import has_api_key

    monkeypatch.delenv("ATOMIC_ATLAS_OFFLINE", raising=False)

    # Default OpenAI endpoint with empty key → False
    monkeypatch.setenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert has_api_key() is False

    # OpenRouter endpoint with placeholder key → True (operator's intent)
    monkeypatch.setenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "unused")
    assert has_api_key() is True

    # Ollama local endpoint with no key → True
    monkeypatch.setenv("OPENAI_API_BASE", "http://localhost:11434/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert has_api_key() is True

    # Offline overrides everything
    monkeypatch.setenv("ATOMIC_ATLAS_OFFLINE", "1")
    assert has_api_key() is False
