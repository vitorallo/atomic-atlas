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
    """All atomics in the repo must parse without error.

    The schema accepts AML.TXXXX[.SUB] for real ATLAS techniques and
    UNCLASSIFIED.<slug> for atomics that don't yet map to a published
    ATLAS technique (see atomics/unclassified/README.md).
    """
    atomics = load_all(ATOMICS_DIR)
    assert len(atomics) >= 9
    for a in atomics:
        assert a.atlas_technique.startswith("AML.T") or a.atlas_technique.startswith("UNCLASSIFIED.")
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


def test_loads_judge_guidance_examples_extractors():
    """The five backfilled atomics carry judge_guidance / judge_examples /
    extractors fields that round-trip through the parser."""
    t0083 = load(ATOMICS_DIR / "AML.T0083" / "direct_chat.md")
    assert t0083.judge_guidance and "credential" in t0083.judge_guidance.lower()
    assert t0083.judge_examples and len(t0083.judge_examples) >= 2
    assert all("verdict" in ex for ex in t0083.judge_examples)
    assert t0083.extractors
    names = {e["name"] for e in t0083.extractors}
    assert "openai_api_key" in names

    t0086 = load(ATOMICS_DIR / "AML.T0086" / "mcp_server.md")
    assert t0086.extractors
    assert {e["name"] for e in t0086.extractors} >= {"passwd_entry", "aws_metadata_imds"}


def test_scoring_field_round_trip(tmp_path):
    """An atomic with a scoring: block must parse and surface the dict."""
    body = (
        "---\n"
        "atlas_technique: AML.T0051.000\n"
        "display_name: Test\n"
        "interaction_vector: direct_chat\n"
        "guid: 11111111-1111-4111-8111-111111111111\n"
        "scoring:\n"
        "  strategy: judge\n"
        "  refusal: true\n"
        "  judge_model: gpt-4o-mini\n"
        "---\n"
        "# Test\n"
    )
    p = tmp_path / "scoring.md"
    p.write_text(body)
    a = load(p)
    assert a.scoring == {
        "strategy": "judge",
        "refusal": True,
        "judge_model": "gpt-4o-mini",
    }
