"""Tests for the .env loader (atomic_atlas.env)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from atomic_atlas.env import load_dotenv


@pytest.fixture
def tmp_dotenv(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "# comment line\n"
        "\n"
        "PLAIN=value1\n"
        "QUOTED_DOUBLE=\"value with spaces\"\n"
        "QUOTED_SINGLE='single quoted'\n"
        "EXPORT_PREFIX=should not be exported tag literally\n"
        "export EXPORTED=exported-value\n"
        "EMPTY=\n"
        "NO_EQUALS_LINE\n"
        "= value-without-key\n",
        encoding="utf-8",
    )
    return p


def test_load_dotenv_writes_keys(tmp_dotenv, monkeypatch):
    monkeypatch.delenv("PLAIN", raising=False)
    monkeypatch.delenv("QUOTED_DOUBLE", raising=False)
    monkeypatch.delenv("QUOTED_SINGLE", raising=False)
    monkeypatch.delenv("EXPORTED", raising=False)
    monkeypatch.delenv("EMPTY", raising=False)

    n = load_dotenv(tmp_dotenv)

    assert n >= 5
    assert os.environ["PLAIN"] == "value1"
    assert os.environ["QUOTED_DOUBLE"] == "value with spaces"
    assert os.environ["QUOTED_SINGLE"] == "single quoted"
    assert os.environ["EXPORTED"] == "exported-value"
    assert os.environ["EMPTY"] == ""


def test_load_dotenv_override_replaces_shell_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRE_SET", "from-shell")
    p = tmp_path / ".env"
    p.write_text("PRE_SET=from-dotenv\n")

    load_dotenv(p, override=True)
    assert os.environ["PRE_SET"] == "from-dotenv"


def test_load_dotenv_no_override_keeps_shell_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PRE_SET", "from-shell")
    p = tmp_path / ".env"
    p.write_text("PRE_SET=from-dotenv\n")

    load_dotenv(p, override=False)
    assert os.environ["PRE_SET"] == "from-shell"


def test_load_dotenv_skip_via_env(tmp_dotenv, monkeypatch):
    monkeypatch.setenv("ATOMIC_ATLAS_SKIP_DOTENV", "1")
    monkeypatch.delenv("PLAIN", raising=False)

    n = load_dotenv(tmp_dotenv)

    assert n == 0
    assert "PLAIN" not in os.environ


def test_load_dotenv_missing_file_returns_zero(tmp_path):
    n = load_dotenv(tmp_path / "does-not-exist")
    assert n == 0


def test_load_dotenv_skips_malformed_lines(tmp_dotenv, monkeypatch):
    """Lines without '=' or with empty key are silently skipped, not errors."""
    monkeypatch.delenv("PLAIN", raising=False)
    n = load_dotenv(tmp_dotenv)
    assert n >= 5  # at least the well-formed ones loaded
