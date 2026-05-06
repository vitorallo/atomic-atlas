"""Execute runbooks: ordered chains of atomics with on-failure policies."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .runbook import Runbook, AtomicRef, resolve_atomic_ref
from .runner import (
    RunResult,
    _ensure_pyrit_initialized,
    resolve_target,
    run_atomic,
)
from .targets.base import require_pyrit


@dataclass
class RunbookStepResult:
    step_id: int
    atomic_path: str
    atlas_technique: str
    interaction_vector: str
    total_runs: int
    successes: int
    failures: int
    errors: int
    duration_seconds: float
    on_failure: str
    skipped: bool = False
    skip_reason: str | None = None

    @property
    def success_rate(self) -> float:
        return self.successes / self.total_runs if self.total_runs else 0.0


@dataclass
class RunbookResult:
    runbook_id: str
    runbook_path: str
    guid: str
    runbook_type: str
    atlas_tactics: list[str]
    step_results: list[RunbookStepResult] = field(default_factory=list)
    chain_success: bool = False
    duration_seconds: float = 0.0
    stopped_at_step: int | None = None


async def run_runbook(
    runbook: Runbook,
    atomics_dir: Path,
    target_profile: dict[str, Any],
    authorized: bool = False,
    hitl: bool = False,
) -> RunbookResult:
    """Execute a runbook against a target.

    Walks the dependency DAG topologically; runs each atomic via the existing
    ``runner.run_atomic``; applies on-failure policies between steps.

    A step is **skipped** if any of its transitive depends_on parents stopped
    the chain (on_failure=stop with zero successes). The skip is recorded
    explicitly in ``step_results`` so reports stay complete.

    When ``hitl=True``, every outbound atomic send is gated by an operator
    prompt. If the operator aborts, the chain stops; remaining steps are
    marked skipped; cleanup runs.
    """
    require_pyrit()
    if not authorized:
        raise PermissionError(
            "Pass authorized=True to confirm you have authorization to test this target."
        )
    _ensure_pyrit_initialized()

    start = time.monotonic()
    result = RunbookResult(
        runbook_id=runbook.runbook_id,
        runbook_path=str(runbook.path),
        guid=runbook.guid,
        runbook_type=runbook.runbook_type,
        atlas_tactics=list(runbook.atlas_tactics),
    )

    order = runbook.topological_order()
    stopped_step_ids: set[int] = set()

    for ref in order:
        # Skip if any depends_on parent is in stopped set (transitive).
        if any(d in stopped_step_ids for d in ref.depends_on):
            stopped_step_ids.add(ref.id)
            result.step_results.append(RunbookStepResult(
                step_id=ref.id,
                atomic_path="(skipped)",
                atlas_technique="-",
                interaction_vector="-",
                total_runs=0,
                successes=0,
                failures=0,
                errors=0,
                duration_seconds=0.0,
                on_failure=ref.on_failure,
                skipped=True,
                skip_reason=f"transitive stop from upstream step(s)",
            ))
            continue

        atomic = resolve_atomic_ref(ref, atomics_dir)
        if ref.runs is not None:
            atomic.runs = ref.runs

        target_obj = resolve_target(atomic, target_profile)
        atomic_result = await run_atomic(atomic, target_obj, authorized=True, hitl=hitl, profile=target_profile)

        step_result = RunbookStepResult(
            step_id=ref.id,
            atomic_path=str(atomic.path),
            atlas_technique=atomic.atlas_technique,
            interaction_vector=atomic.interaction_vector,
            total_runs=atomic_result.total_runs,
            successes=atomic_result.successes,
            failures=atomic_result.failures,
            errors=atomic_result.errors,
            duration_seconds=atomic_result.duration_seconds,
            on_failure=ref.on_failure,
        )

        if atomic_result.successes == 0 and ref.on_failure == "retry":
            retries = ref.retry_max or 1
            for _ in range(retries):
                target_retry = resolve_target(atomic, target_profile)
                retry_result = await run_atomic(atomic, target_retry, authorized=True, hitl=hitl, profile=target_profile)
                step_result.total_runs += retry_result.total_runs
                step_result.successes += retry_result.successes
                step_result.failures += retry_result.failures
                step_result.errors += retry_result.errors
                step_result.duration_seconds += retry_result.duration_seconds
                if retry_result.successes > 0:
                    break

        result.step_results.append(step_result)

        if step_result.successes == 0 and ref.on_failure == "stop":
            stopped_step_ids.add(ref.id)
            if result.stopped_at_step is None:
                result.stopped_at_step = ref.id

    # chain_success: every non-skipped step with on_failure=stop had ≥1 success.
    chain_success = True
    for sr in result.step_results:
        if sr.skipped:
            chain_success = False
            break
        if sr.on_failure == "stop" and sr.successes == 0:
            chain_success = False
            break
    result.chain_success = chain_success
    result.duration_seconds = time.monotonic() - start

    return result
