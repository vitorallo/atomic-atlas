"""Markdown reporter for ``atomic-atlas report --format markdown``.

Renders ``RunResult`` (or list of them) into a stakeholder-readable
markdown document, with per-run Evidence inline (tier, matched
indicators, judge reasoning, extracted artifacts).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional


def render_evidence_block(ev: dict) -> list[str]:
    """Render an Evidence dict as indented markdown bullets under a run line."""
    out: list[str] = []
    tier = ev.get("tier", "?")
    out.append(f"  - tier: `{tier}`")
    if ev.get("refusal_short_circuited"):
        out.append("  - refusal short-circuit fired (primary scorer skipped)")
    matched = ev.get("matched_indicators") or []
    if matched:
        joined = ", ".join(f"`{m}`" for m in matched)
        out.append(f"  - matched indicators: {joined}")
    reasoning = ev.get("judge_reasoning")
    if reasoning:
        compact = reasoning.replace("\n", " ").strip()
        out.append(f"  - judge: {compact[:240]}")
    extracted = ev.get("extracted") or {}
    for name, hits in extracted.items():
        sample = ", ".join(f"`{h}`" for h in hits[:3])
        more = f" (+{len(hits) - 3} more)" if len(hits) > 3 else ""
        out.append(f"  - extracted **{name}**: {sample}{more}")
    return out


def render_markdown(results: Iterable) -> str:
    """Build the full markdown report body. Pure function — no I/O."""
    lines = ["# atomic-atlas results\n"]
    for r in results:
        lines.append(f"## {r.atlas_technique} / {r.interaction_vector}")
        lines.append(f"- Success rate: {r.success_rate:.0%} ({r.successes}/{r.total_runs})")
        if r.errors:
            lines.append(f"- Errors: {r.errors}")
        lines.append(f"- Duration: {r.duration_seconds:.1f}s")
        details = getattr(r, "run_details", None) or []
        if details:
            lines.append("")
            lines.append("### Run details")
            for d in details:
                run_num = d.get("run", "?")
                if "error" in d:
                    phase = d.get("phase", "run")
                    lines.append(f"- Run {run_num} **error** ({phase}): `{d['error']}`")
                else:
                    mark = "✓" if d.get("success") else "✗"
                    preview = d.get("response_preview", "").replace("\n", " ").strip()
                    lines.append(f"- Run {run_num} {mark} — {preview[:160]}")
                    ev = d.get("evidence")
                    if ev:
                        lines.extend(render_evidence_block(ev))
        lines.append("")
    return "\n".join(lines)


def write_or_echo(results: Iterable, output: Optional[str]) -> None:
    """Render then either write to ``output`` or echo via click."""
    import click  # local import; reporters don't otherwise depend on click
    text = render_markdown(results)
    if output:
        Path(output).write_text(text)
        click.echo(f"Report written to {output}")
    else:
        click.echo(text)
