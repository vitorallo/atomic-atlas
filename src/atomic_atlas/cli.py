"""atomic-atlas CLI — recon / exec / report / validate."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
import yaml

ATOMICS_DIR = Path(__file__).parent.parent.parent / "atomics"


@click.group()
def cli():
    """atomic-atlas: ATLAS-keyed agentic vector tests, backed by PyRIT."""


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
def exec_(atomic_path: str, target: str, profile: str | None, runs: int | None,
          output: str, authorized: bool):
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
        profile_data.setdefault("base_url", target)

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
    result = asyncio.run(run_atomic(atomic, target_obj, authorized=True))

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
        lines.append("")
    text = "\n".join(lines)
    if output:
        Path(output).write_text(text)
        click.echo(f"Report written to {output}")
    else:
        click.echo(text)


_ADAPTER_STANZAS = {
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
        "    type: http_registry_stub   # v0.1 placeholder — see SPEC.md\n"
        "    registry_url: http://localhost:9000/mcp/tools\n"
        "    auth:\n"
        "      type: bearer\n"
        "      token: ${MCP_TOKEN}\n"
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
