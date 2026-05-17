"""Findings reporter — engagement-level stakeholder report.

Aggregates an ``Engagement`` directory's ``results.jsonl`` into per-
``(atomic × target)`` ``Finding``s, then renders a markdown report
with a scoreboard and per-finding sections sorted by severity.

Pure function ``render_findings`` returns the document string;
``write_or_echo`` adds the click-coupled "write to file or stdout"
shell.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Optional

from ..finding import (
    Finding,
    aggregate,
    severity_rank,
    VERDICT_VULNERABLE,
    VERDICT_PARTIAL,
    VERDICT_NOT_VULNERABLE,
    VERDICT_INCONCLUSIVE,
)


# ---------------------------------------------------------------------------
# Aggregation entry point
# ---------------------------------------------------------------------------


def aggregate_findings(
    entries: Iterable[dict],
    *,
    atomics_by_path: dict[str, Any],
) -> list[Finding]:
    """Group engagement entries by ``(atomic, target_id)`` and aggregate.

    ``atomics_by_path`` maps ``atomic_path`` strings to AtomicTest objects
    so the reporter can read frontmatter (``severity_floor``) and the
    ``## ATLAS mitigations`` body section. Entries whose atomic_path
    doesn't resolve are skipped (with a stub atomic) rather than crash —
    this lets the reporter run against an engagement directory that has
    drifted from the catalog.
    """
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for entry in entries:
        if entry.get("kind") != "atomic_result":
            continue
        key = (
            entry.get("atomic_path", ""),
            entry.get("atlas_technique", ""),
            entry.get("target_id", ""),
        )
        groups[key].append(entry)

    findings: list[Finding] = []
    for (atomic_path, _technique, target_id), bucket in groups.items():
        atomic = atomics_by_path.get(atomic_path)
        if atomic is None:
            atomic = _stub_atomic(bucket[0])
        findings.append(aggregate(bucket, atomic=atomic, target_id=target_id))

    findings.sort(
        key=lambda f: (-severity_rank(f.severity), f.atlas_technique, f.target_id)
    )
    return findings


def _stub_atomic(entry: dict) -> Any:
    """Stand-in atomic when the catalog file is missing — preserves the
    technique / vector for the report header but recommends nothing."""
    class _Stub:
        atlas_technique = entry.get("atlas_technique", "")
        interaction_vector = entry.get("interaction_vector", "")
        severity_floor = None
        def section(self, _name): return ""
    return _Stub()


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


_VERDICT_LABEL = {
    VERDICT_VULNERABLE: "VULNERABLE",
    VERDICT_PARTIAL: "PARTIALLY VULNERABLE",
    VERDICT_NOT_VULNERABLE: "NOT VULNERABLE",
    VERDICT_INCONCLUSIVE: "INCONCLUSIVE",
}


def _preview(text: str, limit: int) -> str:
    """Single-line preview: collapse newlines, trim, clip with ``…``."""
    s = text.replace("\n", " ").strip()
    return s if len(s) <= limit else s[:limit] + "…"


def render_findings(findings: list[Finding]) -> str:
    """Return the full markdown document. No I/O."""
    if not findings:
        return "# Engagement findings\n\n*No atomic-result entries in this engagement.*\n"

    lines: list[str] = ["# Engagement findings\n"]

    # Scoreboard
    lines.append("| Verdict | Severity | Atomic / vector | Target | Runs |")
    lines.append("|---|---|---|---|---|")
    for f in findings:
        lines.append(
            f"| {_VERDICT_LABEL.get(f.verdict, f.verdict)} | {f.severity.upper()} | "
            f"`{f.atlas_technique}` / `{f.interaction_vector}` | `{f.target_id}` | "
            f"{f.runs_succeeded}/{f.runs_total} |"
        )
    lines.append("")

    # Per-finding sections
    for f in findings:
        lines.extend(_render_finding(f))

    return "\n".join(lines)


def _render_finding(f: Finding) -> list[str]:
    label = _VERDICT_LABEL.get(f.verdict, f.verdict)
    out: list[str] = [
        "---",
        "",
        f"## {label} — `{f.atlas_technique}` / `{f.interaction_vector}` — {f.severity.upper()}",
    ]
    meta_bits = [
        f"Target: `{f.target_id}`",
        f"{f.runs_succeeded}/{f.runs_total} runs succeeded",
        f"{f.duration_seconds:.1f}s",
    ]
    if f.judge_model:
        meta_bits.append(f"judge: `{f.judge_model}`")
    if f.first_run_at:
        meta_bits.append(f"recorded: {f.first_run_at}")
    out.append(" · ".join(meta_bits))
    out.append("")

    out.append(f"**Summary.** {f.summary}")
    out.append("")

    # Terser sections for negative / inconclusive findings.
    if f.verdict in (VERDICT_NOT_VULNERABLE, VERDICT_INCONCLUSIVE):
        if f.recommendations:
            out.append("**ATLAS mitigations referenced for this technique:**")
            for r in f.recommendations[:5]:
                out.append(f"- {r}")
            out.append("")
        return out

    if f.extracted_artifacts:
        out.append("**Evidence captured:**")
        for name, hits in f.extracted_artifacts.items():
            sample = ", ".join(f"`{h}`" for h in hits[:3])
            extra = f" *(+{len(hits) - 3} more)*" if len(hits) > 3 else ""
            out.append(f"- `{name}`: {sample}{extra}")
        out.append("")

    if f.sample_attack_inputs:
        out.append("**Sample attack inputs that landed:**")
        for s in f.sample_attack_inputs[:3]:
            out.append(f"- {_preview(s, 200)}")
        out.append("")

    if f.evidence_excerpts:
        out.append("**Representative response excerpt:**")
        for excerpt in f.evidence_excerpts[:1]:
            out.append(f"> {_preview(excerpt, 320)}")
        out.append("")

    if f.recommendations:
        out.append("**Recommended mitigations** (from atomic's `## ATLAS mitigations`):")
        for r in f.recommendations:
            out.append(f"- {r}")
        out.append("")

    return out


# ---------------------------------------------------------------------------
# Click-coupled write
# ---------------------------------------------------------------------------


def write_or_echo(findings: list[Finding], output: Optional[str]) -> None:
    """Render then either write to ``output`` or echo via click."""
    import click  # local import; reporter doesn't otherwise depend on click
    text = render_findings(findings)
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"Findings report written to {output}")
    else:
        click.echo(text)
