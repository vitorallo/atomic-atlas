"""Shared pytest fixtures.

Repo-pollution guard: several tests exercise CLI code paths
(`exec` / `report`) that call ``Engagement.from_env_or_default()`` with no
explicit override. With no override and cwd at the repo root that resolves to
``./atomic-atlas-engagement/`` and writes a real results.jsonl into the working
tree. This autouse fixture points ``ATOMIC_ATLAS_ENGAGEMENT_DIR`` at a
per-test tmp directory so no test can write engagement output into the repo,
regardless of which code path it hits.

Tests that deliberately assert default/explicit resolution
(``tests/test_engagement.py``) use the same function-scoped ``monkeypatch``
instance and override this within the test body (``delenv`` / explicit path),
so they keep working.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolate_engagement_dir(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "ATOMIC_ATLAS_ENGAGEMENT_DIR", str(tmp_path / "engagement")
    )
