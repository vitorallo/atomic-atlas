"""Local ``.env`` loader for atomic-atlas.

Reads the repo-root ``.env`` once on import and writes its values into
``os.environ``. Per project preference, ``.env`` wins over the existing shell
environment — i.e. when a key is set both places, the value in ``.env``
takes precedence. The real shell env is the *fallback* for keys not present
in ``.env``.

This is the opposite of stock python-dotenv default (``override=False``);
the choice is intentional so an operator who edits ``.env`` doesn't have
to also unset stale shell exports.

To skip this behavior (e.g. in CI where shell env should win), set
``ATOMIC_ATLAS_SKIP_DOTENV=1`` before importing atomic_atlas.

No new dependency — minimal hand-written parser. Supports:

- ``KEY=value``
- ``KEY="quoted value"`` and ``KEY='quoted value'``
- ``# comment`` lines and trailing-comment-free values
- Blank lines

Does NOT support: variable interpolation, multi-line values, ``export``
prefix. Real engagements with complex env should use direct shell exports
or a tool like ``direnv`` instead.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_dotenv(
    path: Path | str | None = None,
    *,
    override: bool = True,
) -> int:
    """Load ``.env`` at *path* into ``os.environ``.

    Returns the number of keys written. If *path* is missing the file or
    ``ATOMIC_ATLAS_SKIP_DOTENV=1`` is set in the env, returns 0 without
    error.
    """
    if os.environ.get("ATOMIC_ATLAS_SKIP_DOTENV") == "1":
        return 0
    p = Path(path) if path else DEFAULT_DOTENV_PATH
    if not p.exists():
        return 0
    count = 0
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # Allow optional `export KEY=value` form.
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip()
        # Strip matched surrounding quotes — but not partial / mismatched.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value
        count += 1
    return count


# Auto-load on first import. Anyone who imports anything from atomic_atlas
# transitively imports this module via cli / runner / mcp_server, so the
# .env values are in os.environ by the time the consumers read them.
_LOADED_COUNT = load_dotenv()
