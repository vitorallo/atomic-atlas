"""Print a 2D technique × vector coverage matrix to the terminal."""

from __future__ import annotations

from ..parser import INTERACTION_VECTORS, load_all
from ..runner import RunResult
from pathlib import Path

ORDERED_VECTORS = [
    "direct_chat", "system_prompt", "rag_corpus", "document_upload",
    "tool_response", "mcp_server", "web_fetch", "webhook",
    "email", "a2a_message", "computer_use", "model_api",
]
SHORT = {
    "direct_chat": "CHAT", "system_prompt": "SYSPROMPT", "rag_corpus": "RAG",
    "document_upload": "DOC", "tool_response": "TOOL", "mcp_server": "MCP",
    "web_fetch": "WEB", "webhook": "HOOK", "email": "EMAIL",
    "a2a_message": "A2A", "computer_use": "SCREEN", "model_api": "MODEL",
}


def print_coverage_matrix(atomics_dir: Path | str, results: list[RunResult] | None = None) -> None:
    atomics = load_all(atomics_dir)

    # Build set of (technique, vector) cells that have atomics
    catalog: dict[tuple[str, str], str] = {}
    for a in atomics:
        catalog[(a.atlas_technique, a.interaction_vector)] = "●"

    # Overlay results if provided
    result_map: dict[tuple[str, str], RunResult] = {}
    if results:
        for r in results:
            result_map[(r.atlas_technique, r.interaction_vector)] = r

    techniques = sorted({a.atlas_technique for a in atomics})
    vectors = [v for v in ORDERED_VECTORS if any((t, v) in catalog for t in techniques)]

    # Header
    col_w = 10
    header = f"{'Technique':<20}" + "".join(f"{SHORT[v]:>{col_w}}" for v in vectors)
    print(header)
    print("-" * len(header))

    for tech in techniques:
        row = f"{tech:<20}"
        for v in vectors:
            key = (tech, v)
            if key in result_map:
                r = result_map[key]
                rate = r.success_rate
                cell = f"{rate:.0%}" if rate > 0 else "0%"
                row += f"{cell:>{col_w}}"
            elif key in catalog:
                row += f"{'○':>{col_w}}"
            else:
                row += f"{'·':>{col_w}}"
        print(row)

    print()
    print("● / ○  atomic exists  ·  no atomic  |  % = success rate from last run")
