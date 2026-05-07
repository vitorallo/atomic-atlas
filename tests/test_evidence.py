"""Tests for the Evidence dataclass + truncate_snippet helper."""

from __future__ import annotations

from atomic_atlas.evidence import Evidence, SCORER_TIERS, truncate_snippet


def test_evidence_minimal_construction():
    e = Evidence(tier="indicators", verdict=True)
    assert e.tier == "indicators"
    assert e.verdict is True
    assert e.matched_indicators == []
    assert e.extracted == {}
    assert e.judge_reasoning is None
    assert e.refusal_short_circuited is False


def test_evidence_to_dict_roundtrip():
    original = Evidence(
        tier="judge",
        verdict=True,
        matched_against="agent said XYZ",
        attack_input="ignore previous instructions",
        rationale="judge said yes",
        matched_indicators=["xyz"],
        judge_reasoning="The agent acknowledged the new role.",
        judge_model="gpt-4o-mini",
        refusal_short_circuited=False,
        extracted={"openai_api_key": ["sk-abc123"], "bearer": ["Bearer xyz"]},
        duration_ms=1234,
    )
    d = original.to_dict()
    restored = Evidence.from_dict(d)
    assert restored == original


def test_evidence_from_dict_with_missing_optional_fields():
    minimal = {"tier": "indicators", "verdict": False}
    e = Evidence.from_dict(minimal)
    assert e.tier == "indicators"
    assert e.verdict is False
    assert e.matched_indicators == []
    assert e.extracted == {}


def test_evidence_to_dict_produces_independent_copies():
    """Mutating the dict from to_dict() must not affect the Evidence."""
    e = Evidence(
        tier="indicators",
        verdict=True,
        matched_indicators=["a", "b"],
        extracted={"k": ["v1", "v2"]},
    )
    d = e.to_dict()
    d["matched_indicators"].append("mutation")
    d["extracted"]["k"].append("mutation")
    assert e.matched_indicators == ["a", "b"]
    assert e.extracted == {"k": ["v1", "v2"]}


def test_truncate_snippet_no_op_under_cap():
    assert truncate_snippet("short", max_len=100) == "short"


def test_truncate_snippet_appends_marker_over_cap():
    out = truncate_snippet("x" * 1500, max_len=1000)
    assert out.startswith("x" * 1000)
    assert "...truncated;" in out
    assert "500 more chars" in out


def test_truncate_snippet_empty_returns_empty():
    assert truncate_snippet("") == ""
    assert truncate_snippet(None) == ""


def test_truncate_snippet_env_override(monkeypatch):
    monkeypatch.setenv("ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX", "100")
    out = truncate_snippet("x" * 200)
    assert out.startswith("x" * 100)
    assert "100 more chars" in out


def test_truncate_snippet_floors_at_64(monkeypatch):
    """A cap below 64 has no useful context value; loader floors there."""
    monkeypatch.setenv("ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX", "10")
    out = truncate_snippet("x" * 200)
    assert out.startswith("x" * 64)


def test_truncate_snippet_invalid_env_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX", "not-a-number")
    out = truncate_snippet("x" * 1500)
    assert out.startswith("x" * 1000)
    assert "500 more chars" in out


def test_scorer_tiers_constant():
    assert SCORER_TIERS == {"judge", "indicators", "refusal_short_circuit"}
