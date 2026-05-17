#!/usr/bin/env python3
"""Regenerate index.yaml — the catalog manifest of every atomic.

The `atomics/` directory is the source of truth; `index.yaml` is a derived,
machine-readable mirror with one row per atomic (technique, vector, path,
guid, display_name, runs). Run after adding or moving atomics.

Usage:
    python scripts/generate_index.py            # rewrite index.yaml
    python scripts/generate_index.py --check    # CI: exit 1 if stale, no write

Reuses atomic_atlas.parser.load_all so discovery/validation stays identical
to the rest of the toolchain.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ATOMICS_DIR = REPO_ROOT / "atomics"
INDEX_PATH = REPO_ROOT / "index.yaml"
SCHEMA_VERSION = 1

sys.path.insert(0, str(REPO_ROOT / "src"))
from atomic_atlas.parser import load_all  # noqa: E402


def build_index() -> dict:
    """Build the index document from parsed atomics, in deterministic order."""
    atomics = sorted(load_all(ATOMICS_DIR), key=lambda a: str(a.path))
    return {
        "version": SCHEMA_VERSION,
        "generated": date.today().isoformat(),
        "atomics": [
            {
                "technique": a.atlas_technique,
                "vector": a.interaction_vector,
                "path": str(a.path.relative_to(REPO_ROOT)),
                "guid": a.guid,
                "display_name": a.display_name,
                "runs": a.runs,
            }
            for a in atomics
        ],
    }


def render(doc: dict) -> str:
    return yaml.safe_dump(doc, sort_keys=False, default_flow_style=False)


def _strip_date(text: str) -> str:
    """Drop the volatile `generated:` line so --check compares content only."""
    return "\n".join(
        ln for ln in text.splitlines() if not ln.startswith("generated:")
    )


def main(argv: list[str]) -> int:
    check = "--check" in argv
    doc = build_index()
    rendered = render(doc)
    n = len(doc["atomics"])

    if check:
        current = INDEX_PATH.read_text() if INDEX_PATH.exists() else ""
        if _strip_date(current) != _strip_date(rendered):
            print(
                "index.yaml is stale — run `python scripts/generate_index.py`.",
                file=sys.stderr,
            )
            return 1
        print(f"index.yaml is up to date ({n} atomics).")
        return 0

    INDEX_PATH.write_text(rendered)
    print(f"Wrote {INDEX_PATH.relative_to(REPO_ROOT)} ({n} atomics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
