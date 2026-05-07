"""Tests for src/atomic_atlas/engagement.py — JSONL append/iterate."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from atomic_atlas.engagement import Engagement, SCHEMA_VERSION


@dataclass
class _StubResult:
    atomic_path: str = "atomics/AML.T0083/direct_chat.md"
    atlas_technique: str = "AML.T0083"
    interaction_vector: str = "direct_chat"
    guid: str = "11111111-1111-4111-8111-111111111111"
    total_runs: int = 3
    successes: int = 2
    failures: int = 1
    errors: int = 0
    duration_seconds: float = 12.3
    run_details: list = field(default_factory=lambda: [{"run": 1, "success": True}])


def test_engagement_resolves_default_to_cwd(tmp_path, monkeypatch):
    monkeypatch.delenv("ATOMIC_ATLAS_ENGAGEMENT_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    e = Engagement.from_env_or_default()
    assert e.root.name == "atomic-atlas-engagement"
    assert e.root.parent == tmp_path


def test_engagement_resolves_explicit_override(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "custom-eng")
    assert e.root == tmp_path / "custom-eng"


def test_engagement_resolves_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("ATOMIC_ATLAS_ENGAGEMENT_DIR", str(tmp_path / "from-env"))
    e = Engagement.from_env_or_default()
    assert e.root == tmp_path / "from-env"


def test_engagement_id_stable_for_same_path(tmp_path):
    e1 = Engagement.from_env_or_default(tmp_path / "x")
    e2 = Engagement.from_env_or_default(tmp_path / "x")
    assert e1.id == e2.id


def test_append_result_creates_jsonl_with_provenance(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "eng")
    r = _StubResult()
    e.append_result(r, atomic_path=r.atomic_path, target_id="dvaa_legacybot",
                    target_url="http://localhost:7003/v1")
    text = e.results_path.read_text()
    line = text.strip().splitlines()[0]
    entry = json.loads(line)
    assert entry["schema_version"] == SCHEMA_VERSION
    assert entry["kind"] == "atomic_result"
    assert entry["atomic_path"] == "atomics/AML.T0083/direct_chat.md"
    assert entry["target_id"] == "dvaa_legacybot"
    assert entry["target_url"] == "http://localhost:7003/v1"
    assert entry["successes"] == 2
    assert entry["run_details"] == [{"run": 1, "success": True}]
    assert "recorded_at" in entry
    assert entry["engagement_id"] == e.id


def test_append_result_accumulates_across_calls(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "eng")
    e.append_result(_StubResult(), atomic_path="a.md", target_id="t1")
    e.append_result(_StubResult(), atomic_path="b.md", target_id="t1")
    e.append_result(_StubResult(), atomic_path="c.md", target_id="t2")
    entries = list(e.all_results())
    assert len(entries) == 3
    assert [x["atomic_path"] for x in entries] == ["a.md", "b.md", "c.md"]


def test_filtered_results_target_id(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "eng")
    e.append_result(_StubResult(), atomic_path="a.md", target_id="t1")
    e.append_result(_StubResult(), atomic_path="b.md", target_id="t2")
    only_t1 = list(e.filtered_results(target_id="t1"))
    assert len(only_t1) == 1
    assert only_t1[0]["target_id"] == "t1"


def test_filtered_results_atlas_technique(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "eng")
    r1 = _StubResult(atlas_technique="AML.T0083")
    r2 = _StubResult(atlas_technique="AML.T0084")
    e.append_result(r1, atomic_path="a.md", target_id="t")
    e.append_result(r2, atomic_path="b.md", target_id="t")
    only_t0083 = list(e.filtered_results(atlas_technique="AML.T0083"))
    assert len(only_t0083) == 1
    assert only_t0083[0]["atlas_technique"] == "AML.T0083"


def test_iter_jsonl_tolerates_corrupted_line(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "eng")
    e.append_result(_StubResult(), atomic_path="a.md", target_id="t")
    # Append a corrupted line directly
    with e.results_path.open("a") as f:
        f.write("not valid json\n")
    e.append_result(_StubResult(), atomic_path="b.md", target_id="t")
    entries = list(e.all_results())
    assert len(entries) == 2  # corrupted line skipped


def test_results_path_and_subdirs_created(tmp_path):
    e = Engagement.from_env_or_default(tmp_path / "eng")
    e.append_result(_StubResult(), atomic_path="a.md", target_id="t")
    assert e.root.is_dir()
    assert e.reports_dir.is_dir()
    assert e.adapted_payloads_dir.is_dir()
    assert e.recon_dir.is_dir()
