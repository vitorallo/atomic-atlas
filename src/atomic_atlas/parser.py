"""Parse atomic markdown files into structured objects."""

from __future__ import annotations

import functools
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
    multi_turn: bool
    sections: dict[str, str]
    payload: str | None = None  # optional explicit payload reference
    success_indicators: list[str] | None = None  # optional explicit scorer hits
    seed_prompt: str | None = None  # optional concrete attack-string used as objective
    judge_guidance: str | None = None  # prose hint prepended to LLM judge true_description
    judge_examples: list[dict[str, str]] | None = None  # {response, verdict, reason} triples
    scoring: dict[str, Any] | None = None  # scoring.strategy / refusal / judge_model
    extractors: list[dict[str, str]] | None = None  # [{name, pattern}] regex extractors

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
        multi_turn=frontmatter.get("multi_turn", True),
        sections=sections,
        payload=frontmatter.get("payload"),
        success_indicators=frontmatter.get("success_indicators"),
        seed_prompt=frontmatter.get("seed_prompt"),
        judge_guidance=frontmatter.get("judge_guidance"),
        judge_examples=frontmatter.get("judge_examples"),
        scoring=frontmatter.get("scoring"),
        extractors=frontmatter.get("extractors"),
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
        # README.md / CHANGELOG.md / etc. are documentation, not atomics.
        # The unclassified/ subtree relies on this to ship a README without
        # the parser trying to load it as an atomic.
        if md_file.name.upper() in {"README.MD", "CHANGELOG.MD", "CONTRIBUTING.MD"}:
            continue
        try:
            tests.append(load(md_file))
        except Exception as exc:
            raise ValueError(f"Failed to load {md_file}: {exc}") from exc
    return tests


@functools.lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any] | None:
    if not _SCHEMA_PATH.exists():
        return None
    import json
    return json.loads(_SCHEMA_PATH.read_text())


def _validate_frontmatter(frontmatter: dict[str, Any], path: Path) -> None:
    schema = _load_schema()
    if schema is None:
        return
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
