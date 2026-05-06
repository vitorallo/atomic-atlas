# Tasks: CLI and Reporting

## Completed
- [x] cli.py — recon / exec / report / validate subcommands
- [x] runner.py — PyRIT orchestration wrapper
- [x] recon.py — vector enumeration + guardrail fingerprinting
- [x] reporters/atlas_navigator.py — Navigator layer JSON
- [x] reporters/coverage_matrix.py — terminal 2D matrix
- [x] skill/atomic-atlas.md — Claude Code skill

## In progress
- [ ] Fix cli.py exec command name collision (Click command named `exec_` but registered as `exec`)

## Pending (v0.1)
- [ ] MCP server stub: list_atomics, read_atomic, recon_target tools
- [ ] Integration test: recon against mock HTTP server
- [ ] Keynote demo dry-run: recon → exec → report against DVAA

## Pending (v0.2)
- [ ] exec: chain support (T0051.001 → T0053 → T0086)
- [ ] exec: cost estimation before run (count API calls, estimate tokens)
- [ ] report: HTML format with embedded Navigator iframe
- [ ] report: auto-generate index.yaml coverage catalog
