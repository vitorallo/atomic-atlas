"""Evidence — first-class data type for scorer output.

Every scored run produces structured Evidence alongside the binary verdict.
Operators attaching findings to engagement reports need to show *what* the
agent said, *what* matched, *what* was extracted (credentials, file content,
system-prompt fragments), and *what* prompt elicited it.

Evidence travels through PyRIT's existing ``Score.score_metadata`` channel
(no PyRIT modifications) → ``RunResult.run_details[i]['evidence']`` →
``RunbookStepResult.evidence_per_run`` → reports.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# Recognized scorer tiers; used for validation in tests and for the Navigator
# reporter's `tier` metadata. Kept as a frozen set rather than an Enum so the
# value is JSON-serializable as-is (a plain string).
SCORER_TIERS: frozenset[str] = frozenset({
    "judge",
    "indicators",
    "substring",
    "composite",
    "refusal_short_circuit",
})

_DEFAULT_SNIPPET_MAX = 1000
_MIN_SNIPPET_MAX = 64  # below this, the snippet has no context value


def truncate_snippet(text: str | None, max_len: int | None = None) -> str:
    """Truncate ``text`` to ``max_len`` chars, appending a truncation marker
    when the original was longer.

    ``max_len`` defaults to ``ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX`` (env) or
    1000 chars. Floors at 64 — below that there's not enough context to be
    useful in a report. Invalid env values fall back to the default rather
    than raising.
    """
    if not text:
        return ""
    if max_len is None:
        env_value = os.environ.get("ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX", "")
        try:
            max_len = int(env_value) if env_value else _DEFAULT_SNIPPET_MAX
        except ValueError:
            max_len = _DEFAULT_SNIPPET_MAX
    if max_len < _MIN_SNIPPET_MAX:
        max_len = _MIN_SNIPPET_MAX
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}\n...truncated; {len(text) - max_len} more chars"


@dataclass
class Evidence:
    """Structured evidence captured alongside a scorer's verdict."""

    tier: str
    verdict: bool
    matched_against: str = ""
    attack_input: str = ""
    rationale: str = ""
    matched_indicators: list[str] = field(default_factory=list)
    judge_reasoning: str | None = None
    judge_model: str | None = None
    refusal_short_circuited: bool = False
    extracted: dict[str, list[str]] = field(default_factory=dict)
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable dict. Lists / dicts are deep-copied so callers
        can mutate the result without affecting this Evidence instance."""
        return {
            "tier": self.tier,
            "verdict": self.verdict,
            "matched_against": self.matched_against,
            "attack_input": self.attack_input,
            "rationale": self.rationale,
            "matched_indicators": list(self.matched_indicators),
            "judge_reasoning": self.judge_reasoning,
            "judge_model": self.judge_model,
            "refusal_short_circuited": self.refusal_short_circuited,
            "extracted": {k: list(v) for k, v in self.extracted.items()},
            "duration_ms": self.duration_ms,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Evidence":
        """Build from a dict produced by ``to_dict`` (or constructed by hand).
        Missing optional keys fall back to defaults."""
        return cls(
            tier=d["tier"],
            verdict=bool(d["verdict"]),
            matched_against=d.get("matched_against", ""),
            attack_input=d.get("attack_input", ""),
            rationale=d.get("rationale", ""),
            matched_indicators=list(d.get("matched_indicators", [])),
            judge_reasoning=d.get("judge_reasoning"),
            judge_model=d.get("judge_model"),
            refusal_short_circuited=bool(d.get("refusal_short_circuited", False)),
            extracted={k: list(v) for k, v in (d.get("extracted") or {}).items()},
            duration_ms=int(d.get("duration_ms", 0)),
        )
