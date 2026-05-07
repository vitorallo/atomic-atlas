# Proposal: CLI and Reporting

## Summary

Deliver the `atomic-atlas` CLI (recon / exec / report / validate), the ATLAS Navigator reporter, the coverage matrix reporter, and the Claude Code skill. These are the user-facing layer — what a practitioner interacts with and what a keynote audience sees.

## Problem

The atomic library and PyRIT targets are unusable without a CLI to invoke them. The keynote demo requires a specific three-command sequence (`recon → exec → report`) that must work end-to-end. The coverage matrix must be renderable so the 6/167 gap narrative is visualizable.

## Proposed solution

Click-based CLI installed as `atomic-atlas` via `pip install atomic-atlas`. Four subcommands. PyRIT-backed exec with authorization gate. ATLAS Navigator layer JSON output. Coverage matrix printed to terminal. Claude Code skill for adaptive execution against novel targets.

## Status

- [x] cli.py (recon / exec / report / validate)
- [x] reporters/atlas_navigator.py
- [x] reporters/coverage_matrix.py
- [x] skill/atomic-atlas.md (Claude Code skill)
- [x] recon.py
- [x] runner.py (PyRIT orchestration wrapper)
- [ ] MCP server stub (v0.1 — list_atomics, read_atomic, recon_target)
