"""atomic-atlas MCP server stub (v0.1).

Run as a stdio MCP server:

    python -m atomic_atlas.mcp_server
    # or, after `pip install`:
    atomic-atlas-mcp

Exposes three read-only tools that mirror the lightweight (no-PyRIT) subset of
the atomic-atlas CLI: ``list_atomics``, ``read_atomic``, ``recon_target``.

Higher-layer agents (Claude, Hermes, GPT-4o, Gemini, AutoGen, LangChain, …)
call these tools to discover atomics and fingerprint a target. Actual
execution (``exec_atomic``) is deferred to v0.2 — it requires a profile/auth
transport design that keeps credentials on the server side.

The MCP SDK package is also named ``mcp``; this module lives inside
``atomic_atlas`` to avoid that name collision.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .parser import load, load_all
from .recon import recon as _recon

# Resolve the atomics directory. By default we look for an ``atomics`` folder
# next to the installed package; users can override via env var when running
# the server outside the repo (e.g., installed catalog path).
_DEFAULT_ATOMICS_DIR = Path(__file__).resolve().parent.parent.parent / "atomics"
ATOMICS_DIR = Path(os.environ.get("ATOMIC_ATLAS_ATOMICS_DIR", str(_DEFAULT_ATOMICS_DIR)))


server = FastMCP("atomic-atlas")


@server.tool()
def list_atomics(
    vector: str | None = None,
    technique: str | None = None,
) -> list[dict[str, Any]]:
    """List atomics in the catalog, optionally filtered by interaction_vector
    or ATLAS technique ID.

    Returns the same shape as ``atomic-atlas list --json``: each entry has
    atlas_technique, display_name, interaction_vector, guid, runs, and a
    relative path that can be passed to ``read_atomic``.
    """
    atomics = load_all(ATOMICS_DIR)
    if vector:
        atomics = [a for a in atomics if a.interaction_vector == vector]
    if technique:
        atomics = [a for a in atomics if a.atlas_technique == technique]
    return [
        {
            "atlas_technique": a.atlas_technique,
            "display_name": a.display_name,
            "interaction_vector": a.interaction_vector,
            "guid": a.guid,
            "runs": a.runs,
            "path": str(a.path.relative_to(ATOMICS_DIR)),
        }
        for a in atomics
    ]


@server.tool()
def read_atomic(path: str) -> dict[str, Any]:
    """Return the full contents of an atomic by its catalog-relative path.

    ``path`` is relative to the atomics/ root (e.g.,
    ``AML.T0051.001/rag_corpus.md``). Returns frontmatter fields plus the
    parsed body sections keyed by H2 heading.
    """
    # Containment: `path` arrives from an MCP tool call (untrusted — the
    # caller may be an LLM agent driven by poisoned content). Resolve and
    # assert the target stays inside the catalog so it can't escape to
    # arbitrary files (e.g. "../../../../etc/passwd" or an absolute path).
    root = ATOMICS_DIR.resolve()
    full_path = (root / path).resolve()
    try:
        full_path.relative_to(root)
    except ValueError:
        raise ValueError(
            f"path must be inside the atomics/ catalog (got {path!r})"
        )
    atomic = load(full_path)
    return {
        "atlas_technique": atomic.atlas_technique,
        "display_name": atomic.display_name,
        "interaction_vector": atomic.interaction_vector,
        "guid": atomic.guid,
        "runs": atomic.runs,
        "target_requires": atomic.target_requires,
        "multi_turn": atomic.multi_turn,
        "sections": atomic.sections,
        "path": str(atomic.path.relative_to(ATOMICS_DIR)),
    }


@server.tool()
def recon_target(
    target: str,
    auth_header: str | None = None,
) -> dict[str, Any]:
    """Fingerprint a target agent: detect exposed entry vectors, fingerprint
    guardrails, and suggest applicable ATLAS techniques.

    ``target`` is the base URL of the target agent. ``auth_header`` is an
    optional Authorization header value (e.g., ``Bearer <token>``). The recon
    module probes a small set of well-known paths; no atomic is executed.
    """
    headers = {"Authorization": auth_header} if auth_header else {}
    result = asyncio.run(_recon(target, auth_headers=headers))
    return {
        "target": target,
        "vectors_detected": result.vectors_detected,
        "vectors_unknown": result.vectors_unknown,
        "vectors_absent": result.vectors_absent,
        "tools_exposed": result.tools_exposed,
        "guardrails": result.guardrails,
        "suggested_techniques": result.suggested_techniques,
    }


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
