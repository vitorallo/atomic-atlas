# Tasks: CLI and Reporting

## Completed
- [x] cli.py — recon / exec / report / validate subcommands
- [x] runner.py — PyRIT orchestration wrapper
- [x] recon.py — vector enumeration + guardrail fingerprinting
- [x] reporters/atlas_navigator.py — Navigator layer JSON
- [x] reporters/coverage_matrix.py — terminal 2D matrix
- [x] skill/atomic-atlas.md — Claude Code skill

## Completed (v0.1, post-architecture-redirect)
- [x] Click `exec_` command name collision fixed (registered as `exec`)
- [x] `atomic-atlas list [--vector V] [--technique T] [--json]` command
- [x] `atomic-atlas runbook` subcommand group (list / show / exec / validate)
- [x] Early profile validation in `exec` — missing adapter config produces an example YAML stanza
- [x] `UnsupportedVectorError` typed exception for adapterless vectors; CLI catches and prints agent-runner hint
- [x] `validate` command skips `_TEMPLATE/`, `payloads/`, and README/CHANGELOG files
- [x] MCP server stub: `atomic-atlas-mcp` exposing `list_atomics`, `read_atomic`, `recon_target` (no PyRIT required)
- [x] Recon module fixes:
  - [x] Real MCP detection via JSON-RPC 2.0 `tools/list` probe to `/`
  - [x] Webhook detection tightened — strict POST + 2xx required (was: any non-500 GET)
  - [x] RAG detection via `/info` and `/agents` metadata endpoints (catches DVAA-style canned-response targets)
- [x] Integration tests for recon against `httpx.MockTransport` (`tests/test_recon.py`, 6 tests)

## Pending (v0.1)
- [ ] Keynote demo dry-run: recon → runbook exec → report against DVAA (architecture verified live; full keynote rehearsal still TODO)

## Pending (v0.2)
- [ ] exec: chain support (T0051.001 → T0053 → T0086)
- [ ] exec: cost estimation before run (count API calls, estimate tokens)
- [ ] report: HTML format with embedded Navigator iframe
- [ ] report: auto-generate index.yaml coverage catalog
