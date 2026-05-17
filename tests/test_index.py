"""Tests for scripts/generate_index.py — the index.yaml catalog generator."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "generate_index", REPO_ROOT / "scripts" / "generate_index.py"
)
generate_index = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generate_index)


def _disk_atomic_paths() -> set[str]:
    out = set()
    for p in (REPO_ROOT / "atomics").rglob("*.md"):
        if "payloads" in p.parts or any(part.startswith("_") for part in p.parts):
            continue
        if p.name.upper() in {"README.MD", "CHANGELOG.MD", "CONTRIBUTING.MD"}:
            continue
        out.add(str(p.relative_to(REPO_ROOT)))
    return out


def test_index_covers_every_atomic_on_disk():
    doc = generate_index.build_index()
    indexed = {row["path"] for row in doc["atomics"]}
    assert indexed == _disk_atomic_paths()


def test_index_rows_have_required_fields():
    doc = generate_index.build_index()
    assert doc["version"] == generate_index.SCHEMA_VERSION
    for row in doc["atomics"]:
        assert set(row) == {
            "technique", "vector", "path", "guid", "display_name", "runs"
        }
        assert row["technique"] and row["vector"] and row["guid"]
        assert isinstance(row["runs"], int)


def test_index_order_is_deterministic():
    a = generate_index.render(generate_index.build_index())
    b = generate_index.render(generate_index.build_index())
    assert a == b
    paths = [r["path"] for r in generate_index.build_index()["atomics"]]
    assert paths == sorted(paths)


def test_committed_index_yaml_is_in_sync():
    """The committed index.yaml must match the generator (content, not date)."""
    committed = (REPO_ROOT / "index.yaml").read_text()
    fresh = generate_index.render(generate_index.build_index())
    assert generate_index._strip_date(committed) == generate_index._strip_date(fresh), (
        "index.yaml is stale — run `python scripts/generate_index.py`"
    )


def test_check_mode_detects_staleness(tmp_path, monkeypatch):
    monkeypatch.setattr(generate_index, "INDEX_PATH", tmp_path / "missing.yaml")
    assert generate_index.main(["--check"]) == 1


def test_generated_yaml_round_trips():
    doc = generate_index.build_index()
    assert yaml.safe_load(generate_index.render(doc)) == doc
