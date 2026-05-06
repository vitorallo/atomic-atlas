"""Tests for the runbook executor — chain orchestration, on-failure policies."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from atomic_atlas.targets.base import PYRIT_AVAILABLE
from atomic_atlas.runbook import load
from atomic_atlas.runner import RunResult

if PYRIT_AVAILABLE:
    from atomic_atlas.runbook_runner import run_runbook, RunbookStepResult


REPO_ROOT = Path(__file__).parent.parent
RUNBOOKS_DIR = REPO_ROOT / "runbooks"
ATOMICS_DIR = REPO_ROOT / "atomics"


def _success_result(atomic, n_success: int = 5, n_total: int = 5) -> RunResult:
    return RunResult(
        atomic_path=str(atomic.path),
        atlas_technique=atomic.atlas_technique,
        interaction_vector=atomic.interaction_vector,
        guid=atomic.guid,
        total_runs=n_total,
        successes=n_success,
        failures=n_total - n_success,
        errors=0,
        duration_seconds=0.5,
    )


PROFILE = {
    "base_url": "http://localhost:7002/v1",
    "adapters": {
        "direct_chat": {
            "type": "openai_compatible",
            "api_key": "unused",
            "model": "test",
        },
    },
}


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="run_runbook needs PyRIT")
@pytest.mark.asyncio
async def test_run_runbook_all_steps_succeed():
    """Two-step runbook where both steps succeed → chain_success=true."""
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-02__api-key-leak.md")

    async def _fake_run(atomic, target, authorized=False, hitl=False, profile=None):
        return _success_result(atomic, n_success=3, n_total=3)

    with patch("atomic_atlas.runbook_runner.run_atomic", side_effect=_fake_run):
        result = await run_runbook(rb, ATOMICS_DIR, PROFILE, authorized=True)

    assert result.chain_success is True
    assert len(result.step_results) == 2
    assert result.stopped_at_step is None
    for sr in result.step_results:
        assert sr.successes == 3


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="run_runbook needs PyRIT")
@pytest.mark.asyncio
async def test_run_runbook_stop_on_failure_aborts_chain():
    """If a step with on_failure=stop has zero successes, downstream steps must
    be marked SKIPPED and chain_success must be false."""
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-02__api-key-leak.md")

    call_log = []

    async def _fake_run(atomic, target, authorized=False, hitl=False, profile=None):
        call_log.append(atomic.atlas_technique)
        # Step 1 (T0084) succeeds; step 2 (T0083) fails.
        if atomic.atlas_technique == "AML.T0083":
            return _success_result(atomic, n_success=0, n_total=5)
        return _success_result(atomic, n_success=3, n_total=3)

    with patch("atomic_atlas.runbook_runner.run_atomic", side_effect=_fake_run):
        result = await run_runbook(rb, ATOMICS_DIR, PROFILE, authorized=True)

    # In L1-02: step 1 is on_failure=continue, step 2 is on_failure=stop.
    # Step 2 fails → chain_success false. No further steps to skip in this runbook
    # (it's only 2 steps) but stopped_at_step is recorded.
    assert result.chain_success is False
    assert result.stopped_at_step == 2
    assert call_log == ["AML.T0084", "AML.T0083"]


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="run_runbook needs PyRIT")
@pytest.mark.asyncio
async def test_run_runbook_continue_failure_keeps_chain_alive():
    """A step with on_failure=continue that fails must NOT kill the chain.
    Downstream steps run; chain_success depends on stop-policy steps only."""
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-02__api-key-leak.md")

    async def _fake_run(atomic, target, authorized=False, hitl=False, profile=None):
        # Step 1 (T0084, on_failure=continue) fails; step 2 (T0083, on_failure=stop) succeeds.
        if atomic.atlas_technique == "AML.T0084":
            return _success_result(atomic, n_success=0, n_total=3)
        return _success_result(atomic, n_success=2, n_total=5)

    with patch("atomic_atlas.runbook_runner.run_atomic", side_effect=_fake_run):
        result = await run_runbook(rb, ATOMICS_DIR, PROFILE, authorized=True)

    # Step 1 failed but on_failure=continue → step 2 still ran and succeeded.
    assert result.chain_success is True
    assert result.stopped_at_step is None
    assert len(result.step_results) == 2
    assert result.step_results[0].successes == 0
    assert result.step_results[1].successes == 2


@pytest.mark.skipif(not PYRIT_AVAILABLE, reason="run_runbook needs PyRIT")
@pytest.mark.asyncio
async def test_run_runbook_requires_authorized():
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-01__system-prompt-extraction.md")
    with pytest.raises(PermissionError):
        await run_runbook(rb, ATOMICS_DIR, PROFILE, authorized=False)
