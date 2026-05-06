"""PyRIT orchestration wrapper for atomic-atlas tests."""

from __future__ import annotations

import asyncio
import importlib
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .parser import AtomicTest, load
from .targets.base import (
    AtomicAtlasTarget,
    PYRIT_AVAILABLE,
    PyRITNotInstalledError,
    require_pyrit,
)


# Vectors with deterministic adapters in src/atomic_atlas/targets/.
# Other vectors are valid in atomic frontmatter but require the agent runner
# (Claude Code skill or MCP server) to execute against arbitrary targets.
ADAPTER_VECTORS = frozenset({
    "rag_corpus",
    "mcp_server",
    "tool_response",
    "document_upload",
    "webhook",
})


class UnsupportedVectorError(Exception):
    """Raised when a vector has no deterministic CLI adapter and must be run
    via the agent runner (Claude Code skill or MCP server)."""

    def __init__(self, vector: str) -> None:
        self.vector = vector
        super().__init__(
            f"Vector '{vector}' has no deterministic CLI adapter. "
            f"Run via the agent runner: `/atomic-atlas` in Claude Code, or "
            f"the atomic-atlas MCP server. CLI adapters exist for: "
            f"{', '.join(sorted(ADAPTER_VECTORS))}."
        )


@dataclass
class RunResult:
    atomic_path: str
    atlas_technique: str
    interaction_vector: str
    guid: str
    total_runs: int
    successes: int
    failures: int
    errors: int
    duration_seconds: float
    run_details: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successes / self.total_runs


def load_profile(profile_path: Path | str) -> dict[str, Any]:
    return yaml.safe_load(Path(profile_path).read_text(encoding="utf-8"))


def _ensure_pyrit_initialized() -> None:
    """Initialize PyRIT central memory once per process.

    PyRIT's PromptTarget.__init__ calls CentralMemory.get_memory_instance(),
    which raises if no memory has been set. atomic-atlas defaults to in-memory
    SQLite — ephemeral and fast, which is the right default for one-shot
    `atomic-atlas exec` invocations. Users who want persistent memory can call
    `CentralMemory.set_memory_instance(...)` themselves before invoking
    runner functions; this helper is a no-op if a memory instance already
    exists.
    """
    require_pyrit()
    from pyrit.memory import CentralMemory, SQLiteMemory
    try:
        CentralMemory.get_memory_instance()
        return  # already initialized
    except (ValueError, AttributeError):
        pass
    db_path = os.environ.get("ATOMIC_ATLAS_PYRIT_DB", ":memory:")
    CentralMemory.set_memory_instance(SQLiteMemory(db_path=db_path))


def resolve_target(atomic: AtomicTest, profile: dict[str, Any]) -> AtomicAtlasTarget:
    """Instantiate the correct AtomicAtlasTarget for the atomic's interaction_vector."""
    _ensure_pyrit_initialized()
    vector = atomic.interaction_vector
    adapters_config = profile.get("adapters", {}).get(vector, {})

    if vector == "rag_corpus":
        from .targets.rag_corpus import RAGCorpusTarget
        payload_file = _resolve_payload(atomic)
        return RAGCorpusTarget(atomic, profile, payload_file)

    if vector == "mcp_server":
        from .targets.mcp_server import MCPServerTarget
        tool_payload = _load_json_payload(atomic, "mcp_tool_description_poison.json")
        return MCPServerTarget(atomic, profile, tool_payload)

    if vector == "tool_response":
        from .targets.tool_response import ToolResponseTarget
        poisoned_response = _load_json_payload(atomic, "tool_response_poison.json")
        return ToolResponseTarget(atomic, profile, poisoned_response)

    if vector == "document_upload":
        from .targets.document_upload import DocumentUploadTarget
        payload_file = _resolve_payload(atomic)
        return DocumentUploadTarget(atomic, profile, payload_file)

    if vector == "webhook":
        from .targets.webhook import WebhookTarget
        webhook_payload = _load_json_payload(atomic, "webhook_payload.json")
        return WebhookTarget(atomic, profile, webhook_payload)

    from .parser import INTERACTION_VECTORS
    if vector in INTERACTION_VECTORS:
        raise UnsupportedVectorError(vector)

    raise ValueError(f"Unknown interaction_vector: {vector}")


async def run_atomic(atomic: AtomicTest, target: AtomicAtlasTarget, authorized: bool = False) -> RunResult:
    """Run an atomic test N times and return a RunResult."""
    require_pyrit()
    if not authorized:
        raise PermissionError(
            "Pass authorized=True to confirm you have authorization to test this target. "
            "Running atomic tests against systems you do not own or have written permission "
            "to test is unethical and likely illegal."
        )

    start = time.monotonic()
    result = RunResult(
        atomic_path=str(atomic.path),
        atlas_technique=atomic.atlas_technique,
        interaction_vector=atomic.interaction_vector,
        guid=atomic.guid,
        total_runs=atomic.runs,
        successes=0,
        failures=0,
        errors=0,
        duration_seconds=0.0,
    )

    try:
        try:
            await target.setup()
        except Exception as exc:
            # Setup failure is a fatal-for-this-atomic error. Don't run N
            # iterations that would all fail with the same root cause; fail
            # fast and surface the cause cleanly. cleanup() still runs in the
            # outer finally so any partially-created state is removed.
            result.errors = atomic.runs
            result.run_details.append({
                "run": 0,
                "error": f"setup failed: {exc}",
                "phase": "setup",
            })
            result.duration_seconds = time.monotonic() - start
            return result

        orchestrator = _build_orchestrator(atomic, target)

        for run_num in range(atomic.runs):
            detail: dict[str, Any] = {"run": run_num + 1}
            try:
                responses = await orchestrator.send_prompts_async(
                    prompt_list=[atomic.section("Interaction") or "Begin the test."]
                )
                scored = await orchestrator.score_prompts_by_orchestrator_id_async(
                    orchestrator_id=orchestrator.get_identifier()["id"]
                )
                success = any(
                    s.get_value() is True or str(s.get_value()).lower() in ("true", "1", "yes")
                    for s in scored
                )
                detail["success"] = success
                detail["response_preview"] = str(responses[0])[:200] if responses else ""
                if success:
                    result.successes += 1
                else:
                    result.failures += 1
            except Exception as exc:
                detail["error"] = str(exc)
                result.errors += 1
            result.run_details.append(detail)
    finally:
        await target.cleanup()

    result.duration_seconds = time.monotonic() - start
    return result


def _build_orchestrator(atomic: AtomicTest, target: AtomicAtlasTarget):
    """Instantiate the PyRIT orchestrator specified in the atomic's frontmatter."""
    from pyrit.orchestrator import PromptSendingOrchestrator, RedTeamingOrchestrator
    from pyrit.score import SubStringScorer

    scorer = SubStringScorer(
        substring=_success_substring(atomic),
        category=atomic.atlas_technique,
    )

    orchestrator_name = atomic.pyrit_orchestrator
    if orchestrator_name == "PromptSendingOrchestrator":
        return PromptSendingOrchestrator(
            prompt_target=target,
            scorers=[scorer],
            verbose=False,
        )
    if orchestrator_name == "RedTeamingOrchestrator":
        return RedTeamingOrchestrator(
            attack_strategy=_attack_strategy(atomic),
            prompt_target=target,
            red_teaming_chat=_default_red_team_chat(),
            scorer=scorer,
            verbose=False,
        )
    raise ValueError(f"Unsupported orchestrator: {orchestrator_name}")


def _success_substring(atomic: AtomicTest) -> str:
    """Extract a simple success substring from the atomic's Success criteria section."""
    criteria = atomic.section("Success criteria")
    for line in criteria.splitlines():
        line = line.strip("- ").strip()
        if line and not line.startswith("OR"):
            return line[:80]
    return "callback.atomic-atlas.test"


def _attack_strategy(atomic: AtomicTest) -> str:
    strategy = atomic.section("Attack strategy")
    return strategy or f"Demonstrate that the ATLAS technique {atomic.atlas_technique} succeeds via {atomic.interaction_vector}."


def _default_red_team_chat():
    """Build the attacker LLM target used by RedTeamingOrchestrator.

    Configured via env:

    - ``ATOMIC_ATLAS_ATTACKER_MODEL`` — model / deployment name (default
      ``gpt-4o``).
    - ``OPENAI_API_BASE`` — endpoint (default ``https://api.openai.com/v1``).
    - ``OPENAI_API_KEY`` — API key.

    To drive the attacker from a non-OpenAI provider (Anthropic, Bedrock,
    Ollama, etc.), point ``OPENAI_API_BASE`` at an OpenAI-compatible proxy
    like LiteLLM or vLLM. PyRIT 0.13 does not ship a first-class Anthropic
    target; the LiteLLM proxy is the recommended interop path until it does.
    """
    from pyrit.prompt_target import OpenAIChatTarget
    return OpenAIChatTarget(
        deployment_name=os.environ.get("ATOMIC_ATLAS_ATTACKER_MODEL", "gpt-4o"),
        endpoint=os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1"),
        api_key=os.environ.get("OPENAI_API_KEY", ""),
    )


def _resolve_payload(atomic: AtomicTest) -> Path:
    """Locate the markdown payload file for an atomic.

    Resolution order:
      1. Explicit ``payload:`` frontmatter field (relative to the atomic's directory).
      2. ``payloads/...`` reference parsed out of the ``## Attack strategy`` body.
      3. A single ``.md`` file in the atomic's ``payloads/`` directory.
    """
    if atomic.payload:
        return atomic.technique_dir / atomic.payload
    strategy = atomic.section("Attack strategy")
    for line in strategy.splitlines():
        if "payloads/" in line:
            import re
            m = re.search(r"payloads/([^\s`]+)", line)
            if m:
                return atomic.payloads_dir / m.group(1)
    candidates = list(atomic.payloads_dir.glob("*.md")) if atomic.payloads_dir.exists() else []
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"No payload file found for {atomic.path}")


def _load_json_payload(atomic: AtomicTest, default_name: str) -> dict[str, Any]:
    """Load a JSON payload for an atomic.

    Resolution order:
      1. Explicit ``payload:`` frontmatter field (must end in ``.json``).
      2. ``payloads/<default_name>`` if present.
      3. A single ``.json`` file in the atomic's ``payloads/`` directory.
    """
    import json
    if atomic.payload and atomic.payload.endswith(".json"):
        explicit = atomic.technique_dir / atomic.payload
        if explicit.exists():
            return json.loads(explicit.read_text())
    candidate = atomic.payloads_dir / default_name
    if candidate.exists():
        return json.loads(candidate.read_text())
    if atomic.payloads_dir.exists():
        candidates = sorted(atomic.payloads_dir.glob("*.json"))
        if len(candidates) == 1:
            return json.loads(candidates[0].read_text())
        if len(candidates) > 1:
            raise FileNotFoundError(
                f"Multiple JSON payloads in {atomic.payloads_dir}; "
                f"expected '{default_name}' or a single .json file, "
                f"or set 'payload:' explicitly in frontmatter."
            )
    raise FileNotFoundError(f"Payload not found: {candidate}")
