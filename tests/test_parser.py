"""Tests for the atomic markdown parser and frontmatter validation."""

import pytest
from pathlib import Path

from atomic_atlas.parser import load, load_all

ATOMICS_DIR = Path(__file__).parent.parent / "atomics"
FLAGSHIP = ATOMICS_DIR / "AML.T0051.001" / "rag_corpus.md"


def test_load_flagship():
    atomic = load(FLAGSHIP)
    assert atomic.atlas_technique == "AML.T0051.001"
    assert atomic.interaction_vector == "rag_corpus"
    assert atomic.runs == 5
    assert atomic.guid


def test_sections_parsed():
    atomic = load(FLAGSHIP)
    assert "Why this matters" in atomic.sections
    assert "Success criteria" in atomic.sections
    assert len(atomic.section("Why this matters")) > 10


def test_load_all_valid():
    """All atomics in the repo must parse without error."""
    atomics = load_all(ATOMICS_DIR)
    assert len(atomics) >= 9
    for a in atomics:
        assert a.atlas_technique.startswith("AML.T")
        assert a.interaction_vector
        assert a.guid


def test_all_guids_unique():
    atomics = load_all(ATOMICS_DIR)
    guids = [a.guid for a in atomics]
    assert len(guids) == len(set(guids)), "Duplicate GUIDs found"


def test_invalid_frontmatter_raises(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("---\natlas_technique: INVALID\nguid: not-a-uuid\n---\n# test\n")
    with pytest.raises(ValueError):
        load(bad, validate=True)
