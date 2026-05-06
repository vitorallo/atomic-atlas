"""Parse atomic markdown files into structured objects."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schema" / "atomic_frontmatter.schema.json"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)

INTERACTION_VECTORS = {
    "direct_chat", "system_prompt", "rag_corpus", "document_upload",
    "tool_response", "mcp_server", "web_fetch", "webhook",
    "email", "a2a_message", "computer_use", "model_api",
}


@dataclass
class AtomicTest:
    path: Path
    atlas_technique: str
    display_name: str
    interaction_vector: str
    guid: str
    runs: int
    target_requires: list[dict[str, str]]
    pyrit_orchestrator: str
    pyrit_scorer: str
    sections: dict[str, str]
    payload: str | None = None  # optional explicit payload reference

    @property
    def technique_dir(self) -> Path:
        return self.path.parent

    @property
    def payloads_dir(self) -> Path:
        return self.technique_dir / "payloads"

    def section(self, name: str) -> str:
        """Return the content of a named body section, or empty string."""
        return self.sections.get(name, "")


def load(path: Path | str, validate: bool = True) -> AtomicTest:
    """Load and parse an atomic markdown file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path}: missing or malformed YAML frontmatter")

    frontmatter: dict[str, Any] = yaml.safe_load(m.group(1))
    body = text[m.end():]

    if validate:
        _validate_frontmatter(frontmatter, path)

    sections = _parse_sections(body)

    return AtomicTest(
        path=path,
        atlas_technique=frontmatter["atlas_technique"],
        display_name=frontmatter["display_name"],
        interaction_vector=frontmatter["interaction_vector"],
        guid=frontmatter["guid"],
        runs=frontmatter.get("runs", 5),
        target_requires=frontmatter.get("target_requires", []),
        pyrit_orchestrator=frontmatter.get("pyrit_orchestrator", "PromptSendingOrchestrator"),
        pyrit_scorer=frontmatter.get("pyrit_scorer", "SubStringScorer"),
        sections=sections,
        payload=frontmatter.get("payload"),
    )


def load_all(atomics_dir: Path | str) -> list[AtomicTest]:
    """Load every atomic markdown file under atomics_dir."""
    atomics_dir = Path(atomics_dir)
    tests = []
    for md_file in sorted(atomics_dir.rglob("*.md")):
        if any(part.startswith("_") for part in md_file.parts):
            continue
        if "payloads" in md_file.parts:
            continue
        try:
            tests.append(load(md_file))
        except Exception as exc:
            raise ValueError(f"Failed to load {md_file}: {exc}") from exc
    return tests


def _validate_frontmatter(frontmatter: dict[str, Any], path: Path) -> None:
    if not _SCHEMA_PATH.exists():
        return
    import json
    schema = json.loads(_SCHEMA_PATH.read_text())
    try:
        jsonschema.validate(frontmatter, schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"{path}: frontmatter validation failed — {exc.message}") from exc


def _parse_sections(body: str) -> dict[str, str]:
    """Split markdown body into sections keyed by H2 heading text."""
    sections: dict[str, str] = {}
    parts = _SECTION_RE.split(body)
    # parts[0] is preamble (ignored), then alternating: heading, content
    it = iter(parts[1:])
    for heading in it:
        content = next(it, "").strip()
        sections[heading.strip()] = content
    return sections
