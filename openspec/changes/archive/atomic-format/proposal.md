# Proposal: Atomic Format

## Summary

Define and stabilize the atomic markdown format — the core schema that every test file in the library must conform to. This is the contribution contract: a practitioner writing a new atomic should be able to do so by reading SPEC.md in under 10 minutes.

## Problem

Without a stable, validated format, the library cannot grow via community contribution. Every PR would require manual review of whether the file is structured correctly. The format must be:
- Machine-validatable (JSON Schema on frontmatter)
- AI-generatable (rich enough in natural language that an LLM can produce a valid atomic from a description)
- Human-writable (no deeper than two levels of nesting; body in plain prose)

## Proposed solution

One `.md` file per `(technique × vector)` cell. YAML frontmatter for machine-readable metadata; markdown body with fixed H2-heading sections for human/LLM-readable content. File path encodes both dimensions. JSON Schema validates frontmatter in CI.

## Why markdown over pure YAML

Pure YAML (Atomic Red Team's approach) produces files that are hard to write manually, hard to read without a renderer, and poorly suited for LLM generation. Markdown with frontmatter gives rich natural language context (the `## Why this matters` section is the most important field for the audience) without sacrificing machine parseability.

## Artifacts produced

- `SPEC.md` — canonical format reference
- `schema/atomic_frontmatter.schema.json` — JSON Schema for CI validation
- `atomics/_TEMPLATE/vector_template.md` — contributor template
- `src/atomic_atlas/parser.py` — reference implementation of the parser
- 12 seed atomics demonstrating the format in practice

## Status

- [x] SPEC.md written
- [x] JSON Schema written
- [x] parser.py written and tested
- [x] 12 seed atomics written
- [ ] _TEMPLATE written
- [ ] CI validation workflow added
