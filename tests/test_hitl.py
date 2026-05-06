"""Tests for the HITL wrapper — gate behavior, abort propagation, approval forwarding."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from atomic_atlas.targets.base import PYRIT_AVAILABLE

if PYRIT_AVAILABLE:
    from atomic_atlas.hitl import HITLAbortError, HITLTargetWrapper
    from atomic_atlas.parser import load
    from atomic_atlas.runner import resolve_target


REPO_ROOT = Path(__file__).parent.parent
ATOMICS_DIR = REPO_ROOT / "atomics"


def _build_wrapped_target():
    """Resolve a real DirectChatTarget and wrap it; the wrapper's send is mocked."""
    profile = {
        "base_url": "http://localhost/v1",
        "adapters": {
            "direct_chat": {"type": "openai_compatible", "api_key": "unused", "model": "test"},
        },
    }
    atomic = load(ATOMICS_DIR / "AML.T0051.000" / "direct_chat.md")
    inner = resolve_target(atomic, profile)
    inner.send_prompt_async = AsyncMock(return_value=["forwarded"])
    return inner


def _fake_click(answers):
    """Build a mock click module that returns answers from a queue."""
    answers_iter = iter(answers)
    click_mock = MagicMock()
    click_mock.echo = MagicMock()
    click_mock.prompt = MagicMock(side_effect=lambda *a, **kw: next(answers_iter))
    return click_mock


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="HITL needs PyRIT-instantiated targets")
@pytest.mark.asyncio
async def test_hitl_yes_forwards_to_inner():
    inner = _build_wrapped_target()
    wrapper = HITLTargetWrapper(inner, click_module=_fake_click(["y"]))

    from pyrit.models import Message, MessagePiece
    msg = Message(message_pieces=[MessagePiece(role="user", original_value="payload-here")])

    result = await wrapper.send_prompt_async(message=msg)

    inner.send_prompt_async.assert_awaited_once()
    assert result == ["forwarded"]


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="HITL needs PyRIT-instantiated targets")
@pytest.mark.asyncio
async def test_hitl_no_returns_synthetic_error_response():
    inner = _build_wrapped_target()
    wrapper = HITLTargetWrapper(inner, click_module=_fake_click(["n"]))

    from pyrit.models import Message, MessagePiece
    msg = Message(message_pieces=[MessagePiece(role="user", original_value="payload-here")])

    result = await wrapper.send_prompt_async(message=msg)

    inner.send_prompt_async.assert_not_awaited()
    assert isinstance(result, list) and len(result) == 1
    assert "[HITL skip" in result[0].message_pieces[0].converted_value


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="HITL needs PyRIT-instantiated targets")
@pytest.mark.asyncio
async def test_hitl_abort_raises_hitl_abort_error():
    inner = _build_wrapped_target()
    wrapper = HITLTargetWrapper(inner, click_module=_fake_click(["a"]))

    from pyrit.models import Message, MessagePiece
    msg = Message(message_pieces=[MessagePiece(role="user", original_value="payload-here")])

    with pytest.raises(HITLAbortError):
        await wrapper.send_prompt_async(message=msg)
    inner.send_prompt_async.assert_not_awaited()


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="HITL needs PyRIT-instantiated targets")
@pytest.mark.asyncio
async def test_hitl_show_then_yes_forwards():
    """`s` (show full) re-prompts; subsequent `y` forwards."""
    inner = _build_wrapped_target()
    wrapper = HITLTargetWrapper(inner, click_module=_fake_click(["s", "y"]))

    from pyrit.models import Message, MessagePiece
    msg = Message(message_pieces=[MessagePiece(role="user", original_value="payload-here")])

    result = await wrapper.send_prompt_async(message=msg)

    inner.send_prompt_async.assert_awaited_once()
    assert result == ["forwarded"]


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="HITL needs PyRIT-instantiated targets")
@pytest.mark.asyncio
async def test_hitl_unrecognized_then_yes_forwards():
    """An invalid input re-prompts; subsequent `y` forwards."""
    inner = _build_wrapped_target()
    wrapper = HITLTargetWrapper(inner, click_module=_fake_click(["maybe", "y"]))

    from pyrit.models import Message, MessagePiece
    msg = Message(message_pieces=[MessagePiece(role="user", original_value="payload-here")])

    result = await wrapper.send_prompt_async(message=msg)

    inner.send_prompt_async.assert_awaited_once()
    assert result == ["forwarded"]


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="HITL needs PyRIT-instantiated targets")
@pytest.mark.asyncio
async def test_hitl_setup_and_cleanup_passthrough():
    """The wrapper forwards setup() and cleanup() to the inner target."""
    inner = _build_wrapped_target()
    inner.setup = AsyncMock()
    inner.cleanup = AsyncMock()
    wrapper = HITLTargetWrapper(inner, click_module=_fake_click([]))

    await wrapper.setup()
    await wrapper.cleanup()

    inner.setup.assert_awaited_once()
    inner.cleanup.assert_awaited_once()
