"""Parse runbook markdown files into structured objects.

A runbook is an ordered chain of atomics with engagement-level success
criteria. See SPEC.md and runbooks/README.md for the format.

Mirrors the design of ``parser.py`` for atomics: frontmatter + body sections,
JSON Schema validation, lazy load_all that skips template / README files.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from .parser import AtomicTest, load as load_atomic, load_all as load_all_atomics

_SCHEMA_PATH = Path(__file__).parent.parent.parent / "schema" / "runbook_frontmatter.schema.json"
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)

_SKIP_NAMES = {"README.MD", "CHANGELOG.MD", "CONTRIBUTING.MD"}


@dataclass
class AtomicRef:
    """A reference to an atomic from inside a runbook step."""

    id: int
    technique: str | None = None
    vector: str | None = None
    atomic_path: str | None = None
    atomic_guid: str | None = None
    runs: int | None = None
    depends_on: list[int] = field(default_factory=list)
    parallel_with: list[int] = field(default_factory=list)
    on_failure: str = "stop"
    retry_max: int | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AtomicRef:
        return cls(
            id=d["id"],
            technique=d.get("technique"),
            vector=d.get("vector"),
            atomic_path=d.get("atomic_path"),
            atomic_guid=d.get("atomic_guid"),
            runs=d.get("runs"),
            depends_on=list(d.get("depends_on", [])),
            parallel_with=list(d.get("parallel_with", [])),
            on_failure=d.get("on_failure", "stop"),
            retry_max=d.get("retry_max"),
        )


@dataclass
class Runbook:
    path: Path
    runbook_id: str
    display_name: str
    runbook_type: str
    guid: str
    target_origin: str | None
    atlas_tactics: list[str]
    atomics: list[AtomicRef]
    success_criteria: str
    sections: dict[str, str]

    def section(self, name: str) -> str:
        return self.sections.get(name, "")

    def topological_order(self) -> list[AtomicRef]:
        """Return atomics in topological order respecting depends_on.

        Stable: among ready steps, the lowest ``id`` is taken first. Raises
        ValueError if any depends_on references an unknown step or if a
        cycle exists.
        """
        by_id = {a.id: a for a in self.atomics}
        for a in self.atomics:
            for d in a.depends_on:
                if d not in by_id:
                    raise ValueError(
                        f"step {a.id} depends_on unknown step {d}"
                    )

        in_degree = {a.id: len(a.depends_on) for a in self.atomics}
        ready = sorted([sid for sid, deg in in_degree.items() if deg == 0])
        order: list[AtomicRef] = []
        while ready:
            current = ready.pop(0)
            order.append(by_id[current])
            for a in self.atomics:
                if current in a.depends_on:
                    in_degree[a.id] -= 1
                    if in_degree[a.id] == 0:
                        ready.append(a.id)
            ready.sort()

        if len(order) != len(self.atomics):
            raise ValueError("dependency cycle detected in runbook atomics")
        return order


def load(path: Path | str, validate: bool = True) -> Runbook:
    """Load and parse a runbook markdown file."""
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
    atomics = [AtomicRef.from_dict(a) for a in frontmatter["atomics"]]

    return Runbook(
        path=path,
        runbook_id=frontmatter["runbook_id"],
        display_name=frontmatter["display_name"],
        runbook_type=frontmatter["runbook_type"],
        guid=frontmatter["guid"],
        target_origin=frontmatter.get("target_origin"),
        atlas_tactics=list(frontmatter.get("atlas_tactics", [])),
        atomics=atomics,
        success_criteria=frontmatter["success_criteria"],
        sections=sections,
    )


def load_all(runbooks_dir: Path | str) -> list[Runbook]:
    """Load every runbook under runbooks_dir, skipping templates + READMEs."""
    runbooks_dir = Path(runbooks_dir)
    if not runbooks_dir.exists():
        return []
    out: list[Runbook] = []
    for md_file in sorted(runbooks_dir.rglob("*.md")):
        if any(part.startswith("_") for part in md_file.parts):
            continue
        if md_file.name.upper() in _SKIP_NAMES:
            continue
        try:
            out.append(load(md_file))
        except Exception as exc:
            raise ValueError(f"Failed to load {md_file}: {exc}") from exc
    return out


def resolve_atomic_ref(ref: AtomicRef, atomics_dir: Path) -> AtomicTest:
    """Resolve an AtomicRef to a concrete AtomicTest.

    Resolution order:
      1. ``atomic_path`` (relative to ``atomics_dir``) if set.
      2. ``atomic_guid`` — search the catalog (rename-stable).
      3. ``technique`` + ``vector`` → ``<atomics_dir>/<technique>/<vector>.md``.
    """
    if ref.atomic_path:
        candidate = atomics_dir / ref.atomic_path
        if not candidate.exists():
            raise ValueError(
                f"step {ref.id}: atomic_path {ref.atomic_path} not found"
            )
        return load_atomic(candidate)

    if ref.atomic_guid:
        for a in load_all_atomics(atomics_dir):
            if a.guid == ref.atomic_guid:
                return a
        raise ValueError(
            f"step {ref.id}: no atomic in catalog with guid {ref.atomic_guid}"
        )

    if ref.technique and ref.vector:
        # AML.TXXXX[.SUB] → atomics/AML.TXXXX[.SUB]/<vector>.md
        # UNCLASSIFIED.<slug> → atomics/unclassified/<slug>/<vector>.md
        if ref.technique.startswith("UNCLASSIFIED."):
            slug = ref.technique.removeprefix("UNCLASSIFIED.")
            candidate = atomics_dir / "unclassified" / slug / f"{ref.vector}.md"
        else:
            candidate = atomics_dir / ref.technique / f"{ref.vector}.md"
        if not candidate.exists():
            raise ValueError(
                f"step {ref.id}: atomic {ref.technique}/{ref.vector} not in catalog"
            )
        return load_atomic(candidate)

    raise ValueError(
        f"step {ref.id}: cannot resolve atomic ref "
        "(need atomic_path, atomic_guid, or technique+vector)"
    )


def _validate_frontmatter(frontmatter: dict[str, Any], path: Path) -> None:
    if not _SCHEMA_PATH.exists():
        return
    import json
    schema = json.loads(_SCHEMA_PATH.read_text())
    try:
        jsonschema.validate(frontmatter, schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(
            f"{path}: frontmatter validation failed — {exc.message}"
        ) from exc


def _parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    parts = _SECTION_RE.split(body)
    it = iter(parts[1:])
    for heading in it:
        content = next(it, "").strip()
        sections[heading.strip()] = content
    return sections
