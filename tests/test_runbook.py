"""Tests for runbook parsing, ref resolution, and DAG validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from atomic_atlas.runbook import (
    AtomicRef,
    Runbook,
    load,
    load_all,
    resolve_atomic_ref,
)

REPO_ROOT = Path(__file__).parent.parent
RUNBOOKS_DIR = REPO_ROOT / "runbooks"
ATOMICS_DIR = REPO_ROOT / "atomics"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_dvaa_runbook_l1_01():
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-01__system-prompt-extraction.md")
    assert rb.runbook_id == "RB-DVAA-L1-01"
    assert rb.runbook_type == "dvaa_challenge"
    assert "discovery" in rb.atlas_tactics
    assert len(rb.atomics) == 1
    assert rb.atomics[0].technique == "AML.T0084"
    assert rb.atomics[0].vector == "direct_chat"


def test_load_dvaa_runbook_l1_02_two_steps():
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-02__api-key-leak.md")
    assert len(rb.atomics) == 2
    assert rb.atomics[1].depends_on == [1]
    assert rb.atomics[0].on_failure == "continue"
    assert rb.atomics[1].on_failure == "stop"


def test_load_all_runbooks_round_trips():
    rbs = load_all(RUNBOOKS_DIR)
    assert len(rbs) >= 3
    ids = {rb.runbook_id for rb in rbs}
    assert "RB-DVAA-L1-01" in ids
    assert "RB-DVAA-L1-02" in ids


def test_topological_order_simple():
    rb = load(RUNBOOKS_DIR / "dvaa" / "L1-02__api-key-leak.md")
    order = rb.topological_order()
    assert [a.id for a in order] == [1, 2]


def test_topological_order_detects_cycle(tmp_path):
    """A runbook with a depends_on cycle must raise ValueError."""
    cyclic = tmp_path / "cyclic.md"
    cyclic.write_text("""---
runbook_id: RB-CYCLE
display_name: Cyclic Runbook
runbook_type: kill_chain
guid: 99999999-9999-4999-8999-999999999999
atomics:
  - id: 1
    technique: AML.T0084
    vector: direct_chat
    depends_on: [2]
    on_failure: stop
  - id: 2
    technique: AML.T0083
    vector: direct_chat
    depends_on: [1]
    on_failure: stop
success_criteria: never reached
---
# Cycle
## Why this matters
test
""")
    rb = load(cyclic, validate=False)
    with pytest.raises(ValueError, match="cycle"):
        rb.topological_order()


def test_topological_order_unknown_dep(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("""---
runbook_id: RB-BAD
display_name: Bad Runbook
runbook_type: kill_chain
guid: 88888888-8888-4888-8888-888888888888
atomics:
  - id: 1
    technique: AML.T0084
    vector: direct_chat
    depends_on: [99]
    on_failure: stop
success_criteria: never reached
---
# bad
## Why this matters
test
""")
    rb = load(bad, validate=False)
    with pytest.raises(ValueError, match="unknown step"):
        rb.topological_order()


def test_resolve_atomic_ref_by_technique_vector():
    ref = AtomicRef(id=1, technique="AML.T0084", vector="direct_chat", on_failure="stop")
    atomic = resolve_atomic_ref(ref, ATOMICS_DIR)
    assert atomic.atlas_technique == "AML.T0084"
    assert atomic.interaction_vector == "direct_chat"


def test_resolve_atomic_ref_missing(tmp_path):
    ref = AtomicRef(id=1, technique="AML.T9999", vector="direct_chat", on_failure="stop")
    with pytest.raises(ValueError, match="not in catalog"):
        resolve_atomic_ref(ref, ATOMICS_DIR)


def test_resolve_atomic_ref_no_resolution_path():
    ref = AtomicRef(id=1, on_failure="stop")
    with pytest.raises(ValueError, match="cannot resolve"):
        resolve_atomic_ref(ref, ATOMICS_DIR)


def test_load_invalid_frontmatter_raises(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("""---
runbook_id: BAD-NO-PREFIX
display_name: Bad
runbook_type: dvaa_challenge
guid: 00000000-0000-4000-8000-000000000000
atomics: []
success_criteria: x
---
# bad
""")
    with pytest.raises(ValueError):
        load(bad, validate=True)


def test_runbook_load_skips_readme():
    """load_all under runbooks/ must skip README.md (catalog docs, not a runbook)."""
    rbs = load_all(RUNBOOKS_DIR)
    paths = [str(rb.path) for rb in rbs]
    assert not any("README.md" in p for p in paths)
