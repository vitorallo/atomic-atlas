"""atomic-atlas CLI — recon / exec / report / validate."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
import yaml

ATOMICS_DIR = Path(__file__).parent.parent.parent / "atomics"
RUNBOOKS_DIR = Path(__file__).parent.parent.parent / "runbooks"


@click.group()
def cli():
    """atomic-atlas: ATLAS-keyed agentic vector tests, backed by PyRIT."""


@cli.group(name="runbook")
def runbook_group():
    """Runbook commands — execute ordered atomic chains."""


@cli.command()
@click.option("--target", required=True, help="Target agent base URL")
@click.option("--auth-header", default=None, help="Authorization header value (Bearer token or API key)")
def recon(target: str, auth_header: str | None):
    """Enumerate entry vectors and fingerprint guardrails for TARGET."""
    from .recon import recon as _recon
    headers = {"Authorization": auth_header} if auth_header else {}
    result = asyncio.run(_recon(target, auth_headers=headers))
    result.print_report()


@cli.command(name="list")
@click.option("--vector", default=None, help="Filter by interaction_vector")
@click.option("--technique", default=None, help="Filter by ATLAS technique ID (e.g. AML.T0051.001)")
@click.option("--json", "as_json", is_flag=True, default=False, help="Emit JSON instead of a human table")
def list_atomics(vector: str | None, technique: str | None, as_json: bool):
    """List atomics in the catalog, optionally filtered by vector or technique."""
    from .parser import load_all
    atomics = load_all(ATOMICS_DIR)
    if vector:
        atomics = [a for a in atomics if a.interaction_vector == vector]
    if technique:
        atomics = [a for a in atomics if a.atlas_technique == technique]

    if as_json:
        payload = [
            {
                "atlas_technique": a.atlas_technique,
                "display_name": a.display_name,
                "interaction_vector": a.interaction_vector,
                "guid": a.guid,
                "runs": a.runs,
                "path": str(a.path.relative_to(ATOMICS_DIR.parent)),
            }
            for a in atomics
        ]
        click.echo(json.dumps(payload, indent=2))
        return

    if not atomics:
        click.echo("No atomics matched the filter.")
        return

    width = max(len(a.atlas_technique) for a in atomics)
    for a in atomics:
        click.echo(
            f"{a.atlas_technique.ljust(width)}  {a.interaction_vector:<16}  "
            f"{a.display_name}"
        )
    click.echo(f"\n{len(atomics)} atomic(s).")


@cli.command(name="exec")
@click.argument("atomic_path")
@click.option("--target", required=True, help="Target agent base URL")
@click.option("--profile", default=None, type=click.Path(exists=True), help="Target profile YAML")
@click.option("--runs", default=None, type=int, help="Override number of runs")
@click.option("--output", default="results.json", show_default=True, help="Output file for results JSON")
@click.option("--authorized", is_flag=True, default=False,
              help="Confirm you are authorized to test this target (required)")
@click.option("--hitl", is_flag=True, default=False,
              help="Human-in-the-loop: confirm each outbound message before send. Useful for engagement work and debugging.")
def exec_(atomic_path: str, target: str, profile: str | None, runs: int | None,
          output: str, authorized: bool, hitl: bool):
    """Run an atomic test against TARGET.

    ATOMIC_PATH: technique/vector, e.g. AML.T0051.001/rag_corpus
    """
    if not authorized:
        click.echo("ERROR: --authorized flag required. Only run against systems you own or have written permission to test.", err=True)
        sys.exit(1)

    from .parser import load
    from .runner import (
        ADAPTER_VECTORS,
        UnsupportedVectorError,
        load_profile,
        resolve_target,
        run_atomic,
    )
    from .targets.base import PYRIT_AVAILABLE, PyRITNotInstalledError

    if not PYRIT_AVAILABLE:
        click.echo(
            "ERROR: PyRIT is required for `exec` but is not installed.\n"
            "Install with: pip install 'atomic-atlas[orchestrator]'\n"
            "(Other commands — list / recon / report / validate — work without PyRIT.)",
            err=True,
        )
        sys.exit(4)

    md_path = _resolve_atomic_path(atomic_path)
    atomic = load(md_path)
    if runs is not None:
        atomic.runs = runs

    profile_data: dict = {"base_url": target, "adapters": {}}
    if profile:
        profile_data = load_profile(profile)
        # --target overrides the profile's base_url. The profile's value is a
        # documented default for repo-shipped profiles; the operator's CLI
        # arg is more recent and more specific. Previously we silently kept
        # the profile's value via setdefault — that surprised users.
        profile_data["base_url"] = target

    if atomic.interaction_vector in ADAPTER_VECTORS:
        adapter_cfg = profile_data.get("adapters", {}).get(atomic.interaction_vector)
        if not adapter_cfg:
            click.echo(
                f"ERROR: vector '{atomic.interaction_vector}' requires adapter "
                f"configuration in --profile. Expected YAML stanza:\n",
                err=True,
            )
            click.echo(_example_adapter_stanza(atomic.interaction_vector), err=True)
            sys.exit(2)

    click.echo(f"Running {atomic.atlas_technique} via {atomic.interaction_vector} ({atomic.runs} runs)…")
    try:
        target_obj = resolve_target(atomic, profile_data)
    except UnsupportedVectorError as exc:
        click.echo(f"ERROR: {exc}", err=True)
        click.echo(
            "\nHint: invoke the agent runner instead:\n"
            "  Claude Code:  /atomic-atlas exec "
            f"{atomic.atlas_technique}/{atomic.interaction_vector} --target {target}\n"
            "  MCP server:   call list_atomics / read_atomic / recon_target tools",
            err=True,
        )
        sys.exit(3)
    result = asyncio.run(run_atomic(atomic, target_obj, authorized=True, hitl=hitl, profile=profile_data))

    click.echo(
        f"\n{'✓' if result.success_rate > 0 else '✗'} "
        f"{result.successes}/{result.total_runs} success "
        f"({result.success_rate:.0%}) in {result.duration_seconds:.1f}s"
    )

    results_path = Path(output)
    existing: list = []
    if results_path.exists():
        existing = json.loads(results_path.read_text())
    existing.append(result.__dict__ | {"run_details": result.run_details})
    results_path.write_text(json.dumps(existing, indent=2))
    click.echo(f"Results written to {results_path}")


@cli.command()
@click.option("--input", "input_file", required=True, type=click.Path(exists=True), help="results.json from exec")
@click.option("--format", "fmt", default="navigator", type=click.Choice(["navigator", "coverage", "markdown"]))
@click.option("--output", default=None, help="Output file (default: stdout)")
def report(input_file: str, fmt: str, output: str | None):
    """Generate a report from exec results."""
    from .runner import RunResult
    from .reporters import to_navigator_layer, print_coverage_matrix

    raw = json.loads(Path(input_file).read_text())
    results = [RunResult(**{k: v for k, v in r.items() if k != "run_details"}) for r in raw]
    for r, raw_r in zip(results, raw):
        r.run_details = raw_r.get("run_details", [])

    if fmt == "navigator":
        layer = to_navigator_layer(results)
        text = json.dumps(layer, indent=2)
        if output:
            Path(output).write_text(text)
            click.echo(f"Navigator layer written to {output}")
        else:
            click.echo(text)

    elif fmt == "coverage":
        print_coverage_matrix(ATOMICS_DIR, results)

    elif fmt == "markdown":
        _markdown_report(results, output)


@cli.command()
@click.argument("atomic_path", default=None, required=False)
def validate(atomic_path: str | None):
    """Validate atomic frontmatter. Validates all atomics if no path given."""
    from .parser import load, load_all

    if atomic_path:
        paths = [_resolve_atomic_path(atomic_path)]
    else:
        paths = [
            p for p in ATOMICS_DIR.rglob("*.md")
            if not any(part.startswith("_") for part in p.parts)
            and "payloads" not in p.parts
            and p.name.upper() not in {"README.MD", "CHANGELOG.MD", "CONTRIBUTING.MD"}
        ]

    errors = 0
    for p in paths:
        try:
            load(p, validate=True)
            click.echo(f"  ✓ {p.relative_to(ATOMICS_DIR)}")
        except Exception as exc:
            click.echo(f"  ✗ {p}: {exc}", err=True)
            errors += 1

    if errors:
        sys.exit(1)
    else:
        click.echo(f"\nAll {len(paths)} atomic(s) valid.")


def _resolve_atomic_path(atomic_path: str) -> Path:
    p = Path(atomic_path)
    if p.exists():
        return p
    candidate = ATOMICS_DIR / atomic_path
    if not candidate.suffix:
        candidate = candidate.with_suffix(".md")
    if candidate.exists():
        return candidate
    raise click.BadParameter(f"Atomic not found: {atomic_path}")


def _render_evidence_block(ev: dict) -> list[str]:
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


def _markdown_report(results, output: str | None) -> None:
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
                        lines.extend(_render_evidence_block(ev))
        lines.append("")
    text = "\n".join(lines)
    if output:
        Path(output).write_text(text)
        click.echo(f"Report written to {output}")
    else:
        click.echo(text)


# ---------------------------------------------------------------------------
# runbook subcommands
# ---------------------------------------------------------------------------


def _resolve_runbook(id_or_path: str):
    from .runbook import load as _rb_load, load_all as _rb_load_all
    p = Path(id_or_path)
    if p.exists():
        return _rb_load(p)
    for rb in _rb_load_all(RUNBOOKS_DIR):
        if rb.runbook_id == id_or_path:
            return rb
    raise click.BadParameter(f"Runbook not found: {id_or_path}")


@runbook_group.command(name="list")
@click.option("--type", "rtype", default=None, help="Filter by runbook_type (dvaa_challenge | kill_chain | engagement)")
@click.option("--tactic", default=None, help="Filter by ATLAS tactic slug")
@click.option("--json", "as_json", is_flag=True, default=False)
def runbook_list(rtype: str | None, tactic: str | None, as_json: bool):
    """List runbooks in the catalog."""
    from .runbook import load_all
    rbs = load_all(RUNBOOKS_DIR)
    if rtype:
        rbs = [r for r in rbs if r.runbook_type == rtype]
    if tactic:
        rbs = [r for r in rbs if tactic in r.atlas_tactics]
    if as_json:
        click.echo(json.dumps([{
            "runbook_id": r.runbook_id,
            "display_name": r.display_name,
            "runbook_type": r.runbook_type,
            "guid": r.guid,
            "atlas_tactics": r.atlas_tactics,
            "atomics_count": len(r.atomics),
            "path": str(r.path.relative_to(RUNBOOKS_DIR.parent)),
        } for r in rbs], indent=2))
        return
    if not rbs:
        click.echo("No runbooks matched the filter.")
        return
    width = max(len(r.runbook_id) for r in rbs)
    for r in rbs:
        click.echo(
            f"{r.runbook_id.ljust(width)}  {r.runbook_type:<16}  "
            f"({len(r.atomics)} step) {r.display_name}"
        )
    click.echo(f"\n{len(rbs)} runbook(s).")


@runbook_group.command(name="show")
@click.argument("runbook_id_or_path")
def runbook_show(runbook_id_or_path: str):
    """Print a runbook with resolved atomic dependency graph."""
    from .runbook import resolve_atomic_ref
    rb = _resolve_runbook(runbook_id_or_path)
    click.echo(f"# {rb.display_name}")
    click.echo(f"id:          {rb.runbook_id}")
    click.echo(f"type:        {rb.runbook_type}")
    click.echo(f"guid:        {rb.guid}")
    if rb.target_origin:
        click.echo(f"origin:      {rb.target_origin}")
    if rb.atlas_tactics:
        click.echo(f"tactics:     {', '.join(rb.atlas_tactics)}")
    click.echo(f"\nAtomic chain ({len(rb.atomics)} steps, topological order):")
    for ref in rb.topological_order():
        try:
            atomic = resolve_atomic_ref(ref, ATOMICS_DIR)
            mark = "✓"
            label = f"{atomic.atlas_technique} / {atomic.interaction_vector}"
        except Exception as resolve_err:
            mark = "✗"
            label = f"UNRESOLVABLE: {resolve_err}"
        deps = f" depends_on={ref.depends_on}" if ref.depends_on else ""
        click.echo(
            f"  [{mark}] step {ref.id} on_failure={ref.on_failure}{deps}: {label}"
        )
    click.echo(f"\nSuccess criteria:\n  {rb.success_criteria}")


@runbook_group.command(name="exec")
@click.argument("runbook_id_or_path")
@click.option("--target", required=True, help="Target agent base URL")
@click.option("--profile", default=None, type=click.Path(exists=True), help="Target profile YAML")
@click.option("--output", default="runbook-results.json", show_default=True)
@click.option("--authorized", is_flag=True, default=False,
              help="Confirm you are authorized to test this target (required)")
@click.option("--hitl", is_flag=True, default=False,
              help="Human-in-the-loop: confirm each outbound message before send. Aborts propagate through the chain.")
def runbook_run(runbook_id_or_path: str, target: str, profile: str | None,
                output: str, authorized: bool, hitl: bool):
    """Execute a runbook against TARGET."""
    if not authorized:
        click.echo("ERROR: --authorized flag required.", err=True)
        sys.exit(1)
    from .targets.base import PYRIT_AVAILABLE
    if not PYRIT_AVAILABLE:
        click.echo(
            "ERROR: PyRIT is required for runbook execution but is not installed.\n"
            "Install with: pip install 'atomic-atlas[orchestrator]'",
            err=True,
        )
        sys.exit(4)

    from .runbook_runner import run_runbook
    from .runner import load_profile

    rb = _resolve_runbook(runbook_id_or_path)
    profile_data: dict = {"base_url": target, "adapters": {}}
    if profile:
        profile_data = load_profile(profile)
        profile_data["base_url"] = target  # --target overrides profile default

    click.echo(f"Running runbook {rb.runbook_id} ({len(rb.atomics)} step)…")
    result = asyncio.run(run_runbook(rb, ATOMICS_DIR, profile_data, authorized=True, hitl=hitl))

    mark = "✓" if result.chain_success else "✗"
    click.echo(
        f"\n{mark} chain_success={result.chain_success}  "
        f"({result.duration_seconds:.1f}s)"
    )
    for sr in result.step_results:
        if sr.skipped:
            click.echo(f"  step {sr.step_id} SKIPPED ({sr.skip_reason})")
            continue
        bar = "✓" if sr.successes > 0 else "✗"
        click.echo(
            f"  {bar} step {sr.step_id} {sr.atlas_technique}/{sr.interaction_vector} "
            f"{sr.successes}/{sr.total_runs} ({sr.success_rate:.0%}) "
            f"in {sr.duration_seconds:.1f}s"
        )

    payload = {
        "runbook_id": result.runbook_id,
        "runbook_path": result.runbook_path,
        "guid": result.guid,
        "runbook_type": result.runbook_type,
        "atlas_tactics": result.atlas_tactics,
        "chain_success": result.chain_success,
        "stopped_at_step": result.stopped_at_step,
        "duration_seconds": result.duration_seconds,
        "step_results": [vars(sr) for sr in result.step_results],
    }
    Path(output).write_text(json.dumps(payload, indent=2))
    click.echo(f"Results written to {output}")


@runbook_group.command(name="validate")
@click.argument("runbook_path", default=None, required=False)
def runbook_validate(runbook_path: str | None):
    """Validate runbook frontmatter, atomic-ref resolution, and DAG shape."""
    from .runbook import load, resolve_atomic_ref
    if runbook_path:
        paths = [Path(runbook_path)]
    else:
        paths = [
            p for p in RUNBOOKS_DIR.rglob("*.md")
            if not any(part.startswith("_") for part in p.parts)
            and p.name.upper() not in {"README.MD", "CHANGELOG.MD", "CONTRIBUTING.MD"}
        ]
    errors = 0
    for p in paths:
        try:
            rb = load(p)
            for ref in rb.atomics:
                resolve_atomic_ref(ref, ATOMICS_DIR)
            rb.topological_order()
            click.echo(f"  ✓ {p.relative_to(RUNBOOKS_DIR)}")
        except Exception as validation_err:
            click.echo(f"  ✗ {p}: {validation_err}", err=True)
            errors += 1
    if errors:
        sys.exit(1)
    else:
        click.echo(f"\nAll {len(paths)} runbook(s) valid.")


# ---------------------------------------------------------------------------
# (back to main module body)
# ---------------------------------------------------------------------------


_ADAPTER_STANZAS = {
    "direct_chat": (
        "adapters:\n"
        "  direct_chat:\n"
        "    type: openai_compatible\n"
        "    api_key: ${OPENAI_API_KEY}\n"
        "    model: gpt-4o\n"
        "    # endpoint: optional override; defaults to {base_url}/v1/chat/completions\n"
    ),
    "rag_corpus": (
        "adapters:\n"
        "  rag_corpus:\n"
        "    type: chroma          # or azure_search | http_ingest\n"
        "    base_url: http://localhost:8000\n"
        "    collection: knowledge\n"
    ),
    "mcp_server": (
        "adapters:\n"
        "  mcp_server:\n"
        "    # Mode A — v0.1 placeholder (no real MCP HTTP registration spec):\n"
        "    type: http_registry_stub\n"
        "    registry_url: http://localhost:9000/mcp/tools\n"
        "    auth: { type: bearer, token: ${MCP_TOKEN} }\n"
        "    # Mode B — real MCP JSON-RPC 2.0 over HTTP (e.g. DVAA ToolBot):\n"
        "    # type: mcp_jsonrpc\n"
        "    # base_url: http://localhost:7010\n"
        "    # target_tool: read_file\n"
        "    # tool_arguments: { path: /etc/passwd }\n"
        "    # register_tool: { name: ComplianceLogger, description: ..., inputSchema: {} }\n"
    ),
    "tool_response": (
        "adapters:\n"
        "  tool_response:\n"
        "    port: 9090\n"
        "    base_url: http://localhost:8080\n"
    ),
    "document_upload": (
        "adapters:\n"
        "  document_upload:\n"
        "    upload_url: http://localhost:8080/v1/files\n"
        "    auth:\n"
        "      type: bearer\n"
        "      token: ${UPLOAD_TOKEN}\n"
    ),
    "webhook": (
        "adapters:\n"
        "  webhook:\n"
        "    webhook_url: http://localhost:8080/inbound\n"
        "    callback_port: 9091\n"
    ),
}


def _example_adapter_stanza(vector: str) -> str:
    return _ADAPTER_STANZAS.get(vector, f"# (no example for vector: {vector})")


def main():
    cli()
