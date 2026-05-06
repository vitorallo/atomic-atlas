"""Smoke tests for the reporter modules — Navigator JSON shape and coverage
matrix smoke."""

from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

from atomic_atlas.reporters import to_navigator_layer, print_coverage_matrix
from atomic_atlas.runner import RunResult


ATOMICS_DIR = Path(__file__).parent.parent / "atomics"


def _result(technique: str, vector: str, successes: int = 3, total: int = 5) -> RunResult:
    return RunResult(
        atomic_path=f"atomics/{technique}/{vector}.md",
        atlas_technique=technique,
        interaction_vector=vector,
        guid="00000000-0000-4000-8000-000000000000",
        total_runs=total,
        successes=successes,
        failures=total - successes,
        errors=0,
        duration_seconds=1.5,
    )


def test_navigator_layer_basic_shape():
    """The Navigator layer must be a dict with the keys ATLAS Navigator
    expects: name, domain, techniques (list)."""
    results = [_result("AML.T0051.001", "rag_corpus", 4, 5)]
    layer = to_navigator_layer(results)

    assert isinstance(layer, dict)
    assert "name" in layer
    assert "domain" in layer
    assert "techniques" in layer
    assert isinstance(layer["techniques"], list)
    assert layer["techniques"], "expected at least one technique entry"

    entry = layer["techniques"][0]
    # Navigator strips the AML. prefix because domain=mitre-atlas implies it.
    assert entry["techniqueID"] == "T0051.001"


def test_navigator_layer_uses_atlas_domain():
    """ATLAS layers MUST set domain=mitre-atlas, not enterprise-attack —
    Navigator selects the technique catalog from this field."""
    layer = to_navigator_layer([_result("AML.T0093", "webhook")])
    assert "atlas" in layer["domain"].lower()


def test_navigator_layer_color_reflects_success():
    """Higher success rate → distinct color from a zero-success run, so the
    Navigator visualization is meaningful."""
    high = to_navigator_layer([_result("AML.T0051.001", "rag_corpus", 5, 5)])
    none = to_navigator_layer([_result("AML.T0051.001", "rag_corpus", 0, 5)])
    high_color = high["techniques"][0].get("color")
    none_color = none["techniques"][0].get("color")
    # Either the colors differ, or scores differ — both are valid signals.
    if high_color and none_color:
        assert high_color != none_color
    else:
        assert high["techniques"][0].get("score") != none["techniques"][0].get("score")


def test_coverage_matrix_runs_without_results():
    """print_coverage_matrix must not crash when given an empty results list —
    it should render the catalog with all cells marked as 'atomic only'."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        print_coverage_matrix(ATOMICS_DIR, [])
    output = buf.getvalue()
    # Should mention at least one of the seeded techniques.
    assert "AML.T" in output


def test_coverage_matrix_runs_with_results():
    """With results in hand, print_coverage_matrix should still produce
    output that includes the technique IDs."""
    results = [
        _result("AML.T0051.001", "rag_corpus", 4, 5),
        _result("AML.T0093", "webhook", 0, 5),
    ]
    buf = io.StringIO()
    with redirect_stdout(buf):
        print_coverage_matrix(ATOMICS_DIR, results)
    output = buf.getvalue()
    # Coverage matrix may show full IDs ("AML.T0051.001") or short IDs
    # ("T0051.001"). Either is valid output.
    assert "T0051.001" in output
    assert "T0093" in output
