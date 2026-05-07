"""Engagement memory — accumulates atomic-atlas runs across invocations.

An "engagement" is a directory on disk that collects everything an
operator produces against one or more targets over the course of a
red-team engagement: per-atomic results, runbook results, adapted
payloads, recon dumps, rendered reports.

```
atomic-atlas-engagement/
    results.jsonl           # one JSON object per atomic run
    runbook-results.jsonl   # one JSON object per runbook step
    adapted-payloads/       # bundles produced by `adapt --output`
    recon/                  # JSON outputs of `recon`
    reports/                # rendered findings / navigator / markdown
```

Why JSONL over JSON: append-friendly (no read-modify-write race),
parseable line-by-line by ``jq`` / ``grep``, schema-stable across
versions. Each line is a complete, self-describing record stamped with
``schema_version`` so future migrations can detect old entries.

The engagement dir resolves from ``--engagement`` flag, then
``ATOMIC_ATLAS_ENGAGEMENT_DIR`` env, then the cwd default
``./atomic-atlas-engagement/``. The dir auto-initializes on first
write — no separate ``init`` step required.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional


SCHEMA_VERSION = 1
DEFAULT_DIR_NAME = "atomic-atlas-engagement"


@dataclass(frozen=True)
class Engagement:
    """A directory that accumulates atomic-atlas results across runs."""

    root: Path

    @property
    def id(self) -> str:
        """Stable, human-readable engagement identifier derived from the
        absolute path. Used to stamp result entries so a single
        ``results.jsonl`` line is self-locating even after copy-paste."""
        absolute = str(self.root.resolve())
        digest = hashlib.sha1(absolute.encode("utf-8")).hexdigest()[:10]
        return f"{self.root.name}-{digest}"

    @property
    def results_path(self) -> Path:
        return self.root / "results.jsonl"

    @property
    def runbook_results_path(self) -> Path:
        return self.root / "runbook-results.jsonl"

    @property
    def reports_dir(self) -> Path:
        return self.root / "reports"

    @property
    def adapted_payloads_dir(self) -> Path:
        return self.root / "adapted-payloads"

    @property
    def recon_dir(self) -> Path:
        return self.root / "recon"

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def from_env_or_default(cls, override: Optional[Path | str] = None) -> "Engagement":
        """Resolve the engagement dir using the documented precedence:

        ``override`` > ``ATOMIC_ATLAS_ENGAGEMENT_DIR`` env > cwd default.

        The directory does not have to exist yet — it gets created on
        first write. This lets ``atomic-atlas exec`` work in a fresh
        repo without a separate setup step.
        """
        if override is not None:
            root = Path(override)
        else:
            env = os.environ.get("ATOMIC_ATLAS_ENGAGEMENT_DIR")
            root = Path(env) if env else Path.cwd() / DEFAULT_DIR_NAME
        return cls(root=root)

    def ensure(self) -> None:
        """Create the engagement directory tree if absent. Idempotent."""
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in (self.reports_dir, self.adapted_payloads_dir, self.recon_dir):
            sub.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # append
    # ------------------------------------------------------------------

    def append_result(
        self,
        result: Any,
        *,
        atomic_path: str,
        target_id: str,
        target_url: Optional[str] = None,
    ) -> None:
        """Append one atomic ``RunResult`` entry to ``results.jsonl``.

        ``result`` is duck-typed: anything with ``__dict__`` and
        ``run_details`` works. We don't import ``RunResult`` to keep
        this module independent of the runner.
        """
        # Splat result.__dict__ first, then let our explicit kwargs win
        # (result may carry its own atomic_path/target_id that we want to override).
        entry = self._stamp({
            "kind": "atomic_result",
            **{k: v for k, v in result.__dict__.items() if k != "run_details"},
            "atomic_path": atomic_path,
            "target_id": target_id,
            "target_url": target_url,
            "run_details": result.run_details,
        })
        self._append_jsonl(self.results_path, entry)

    def append_runbook_result(
        self,
        rb_result: Any,
        *,
        target_id: str,
        target_url: Optional[str] = None,
    ) -> None:
        """Append one ``RunbookResult`` entry to ``runbook-results.jsonl``."""
        # RunbookResult has nested step_results; serialize each step explicitly.
        step_payload = []
        for sr in rb_result.step_results:
            step_payload.append({
                **{k: v for k, v in sr.__dict__.items() if k != "evidence_per_run"},
                "evidence_per_run": sr.evidence_per_run,
            })
        entry = self._stamp({
            "kind": "runbook_result",
            "runbook_id": rb_result.runbook_id,
            "runbook_path": rb_result.runbook_path,
            "guid": rb_result.guid,
            "runbook_type": rb_result.runbook_type,
            "atlas_tactics": list(rb_result.atlas_tactics),
            "target_id": target_id,
            "target_url": target_url,
            "chain_success": rb_result.chain_success,
            "duration_seconds": rb_result.duration_seconds,
            "stopped_at_step": rb_result.stopped_at_step,
            "step_results": step_payload,
        })
        self._append_jsonl(self.runbook_results_path, entry)

    def _stamp(self, entry: dict) -> dict:
        """Add provenance metadata to an entry (engagement id, timestamps,
        schema version, command-line invocation)."""
        return {
            "schema_version": SCHEMA_VERSION,
            "engagement_id": self.id,
            "recorded_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "command": " ".join(sys.argv) if sys.argv else "",
            **entry,
        }

    def _append_jsonl(self, path: Path, entry: dict) -> None:
        self.ensure()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str))
            f.write("\n")

    # ------------------------------------------------------------------
    # iterate
    # ------------------------------------------------------------------

    def all_results(self) -> Iterator[dict]:
        """Yield every entry in ``results.jsonl``, oldest first."""
        yield from self._iter_jsonl(self.results_path)

    def all_runbook_results(self) -> Iterator[dict]:
        """Yield every entry in ``runbook-results.jsonl``, oldest first."""
        yield from self._iter_jsonl(self.runbook_results_path)

    def filtered_results(
        self,
        *,
        target_id: Optional[str] = None,
        atlas_technique: Optional[str] = None,
        since: Optional[str] = None,
    ) -> Iterator[dict]:
        """Yield results matching all provided filters. ``since`` is an
        ISO-8601 timestamp prefix (lexicographic comparison; works for
        both ``2026-05-07`` and ``2026-05-07T13:00:00Z``)."""
        for entry in self.all_results():
            if target_id and entry.get("target_id") != target_id:
                continue
            if atlas_technique and entry.get("atlas_technique") != atlas_technique:
                continue
            if since and entry.get("recorded_at", "") < since:
                continue
            yield entry

    def _iter_jsonl(self, path: Path) -> Iterator[dict]:
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    # Tolerate corrupted lines — skip rather than abort
                    # the whole iterator. A real engagement would be
                    # corrupted by a crash mid-write at most once.
                    continue
