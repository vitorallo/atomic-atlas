"""Base class for all atomic-atlas PyRIT targets.

PyRIT is an *optional* runtime dependency. Importing this module without PyRIT
installed must succeed so that ``atomic-atlas list / recon / report / validate``
and the MCP server work in lightweight installs. Instantiating a target — or
running ``atomic-atlas exec`` — requires PyRIT and will raise
``PyRITNotInstalledError`` with a clear install hint.
"""

from __future__ import annotations

import abc
from typing import Any

try:
    from pyrit.prompt_target import PromptTarget
    PYRIT_AVAILABLE = True
except ImportError:  # pragma: no cover — exercised only in lightweight installs
    PromptTarget = object  # type: ignore[assignment,misc]
    PYRIT_AVAILABLE = False

from ..parser import AtomicTest


class PyRITNotInstalledError(RuntimeError):
    """Raised when a code path requires PyRIT but it is not installed.

    Resolution: ``pip install 'atomic-atlas[orchestrator]'``
    """

    def __init__(self) -> None:
        super().__init__(
            "PyRIT is required for atomic execution but is not installed. "
            "Install with: pip install 'atomic-atlas[orchestrator]'"
        )


def require_pyrit() -> None:
    """Raise PyRITNotInstalledError if PyRIT is not importable."""
    if not PYRIT_AVAILABLE:
        raise PyRITNotInstalledError()


class AtomicAtlasTarget(PromptTarget):  # type: ignore[misc]
    """
    Base class for agentic vector targets.

    Extends PyRIT's PromptTarget with:
    - ATLAS technique metadata
    - setup() / cleanup() lifecycle for vector-specific state
    - A target profile dict for adapter configuration and auth

    Instantiation requires PyRIT to be installed. The class body itself is safe
    to import in a lightweight install (PromptTarget falls back to ``object``
    when PyRIT is not available).
    """

    def __init__(self, atomic: AtomicTest, target_profile: dict[str, Any]) -> None:
        require_pyrit()
        super().__init__()
        self.atomic = atomic
        self.profile = target_profile
        self._adapter_config = target_profile.get("adapters", {}).get(
            atomic.interaction_vector, {}
        )

    @abc.abstractmethod
    async def setup(self) -> None:
        """Prepare the entry vector (inject document, start mock server, register tool, etc.)."""

    @abc.abstractmethod
    async def cleanup(self) -> None:
        """Restore the target to its pre-test state."""

    @abc.abstractmethod
    async def send_prompt_async(self, *, prompt_request):  # type: ignore[no-untyped-def]
        """Deliver the interaction turn to the agent and return its response.

        The signature uses ``PromptRequestResponse`` from ``pyrit.models`` at
        runtime; the annotation is intentionally untyped here so the module
        imports cleanly without PyRIT installed (combined with
        ``from __future__ import annotations``).
        """

    def _resolve_env(self, value: str) -> str:
        """Expand ${ENV_VAR} references in config values."""
        import os
        import re
        return re.sub(r"\$\{(\w+)\}", lambda m: os.environ.get(m.group(1), m.group(0)), value)

    def _auth_headers(self) -> dict[str, str]:
        """Build HTTP auth headers from the adapter config."""
        auth = self._adapter_config.get("auth", {})
        if not auth:
            api_key = self._adapter_config.get("api_key")
            if api_key:
                return {"Authorization": f"Bearer {self._resolve_env(api_key)}"}
            return {}
        auth_type = auth.get("type", "bearer")
        if auth_type == "bearer":
            token = self._resolve_env(auth.get("token", ""))
            return {"Authorization": f"Bearer {token}"}
        if auth_type == "api_key":
            header = auth.get("header", "X-API-Key")
            key = self._resolve_env(auth.get("key", ""))
            return {header: key}
        return {}
