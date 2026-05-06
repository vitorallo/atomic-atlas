# Proposal: Agent Runner

## Summary

Two implementations of an adaptive agent runner that drives the atomic-atlas library:

1. **Claude Code skill** (`skill/atomic-atlas.md`) — invoked via `/atomic-atlas` inside a Claude Code session. Uses the `.claude/skills/` mechanism; Claude Code only.
2. **MCP server** (`mcp/server.py`) — generic transport. Exposes atomic-atlas operations as MCP tools so any MCP-capable agent (Hermes, GPT-4o, Gemini, AutoGen, LangChain, etc.) can drive a red-team session.

Both implementations wrap the same interface: the **atomic-atlas CLI**. The CLI is the deterministic primitive layer; the agent reasons above it. This proposal supersedes the prior framing of "two parallel runners" — that was a duplication smell.

## Problem

The agent (skill or MCP) and the CLI started life as parallel implementations: the skill prompted Claude to read atomics directly, probe the target via raw `curl`, generate payloads, deliver them, evaluate semantically, and report — all bypassing `runner.py` entirely. The CLI ran the same workflow through PyRIT but punted 7 of 12 vectors with `NotImplementedError`. Two paths, neither aware of the other; the skill duplicated what the runner already did, and any change to either had to be replicated to the other.

## Proposed solution: agent-on-CLI

Invert the dependency arrow. The CLI is the contract; the agent calls it.

```
agent (skill / MCP server)
  ├── atomic-atlas list                          # discover atomics
  ├── atomic-atlas recon --target X              # fingerprint
  ├── REASONING: which atomic, which adapter, which payload variant
  ├── (writes target profile YAML to a tempfile)
  ├── atomic-atlas exec ATOMIC --profile tmp.yaml --authorized
  ├── reads results.json
  ├── if UnsupportedVectorError or unknown backend: falls back to
  │   manual delivery (one-off Python or curl), still records the run
  └── atomic-atlas report --format navigator
```

The agent only bypasses the CLI when:
- The vector has no deterministic adapter (`direct_chat`, `system_prompt`, `web_fetch`, `email`, `a2a_message`, `computer_use`, `model_api`)
- The target uses a backend the CLI adapter doesn't know (e.g., Weaviate when adapters are chroma / azure_search / http_ingest)
- Semantic success scoring is required and `SubStringScorer` is too weak

In every other case the agent shells out to the CLI. This is the same pattern Atomic Red Team uses with Invoke-AtomicTest.

## Why MCP over a Python SDK adapter

A Python SDK adapter would require Hermes (or any other agent) to import atomic-atlas as a library and call it programmatically — same-process, same-language. An MCP server is transport-agnostic: any agent that speaks MCP can use it, including agents that are sandboxed, cloud-hosted, or written in a different language. MCP is the right boundary for agent-to-tool interop in 2026.

## v0.1 MCP server scope

The MCP server is **lightweight** — it must run without PyRIT installed (PyRIT is now an optional `[orchestrator]` extra). v0.1 exposes three read-only tools:

| MCP tool | Wraps | Needs PyRIT? |
|---|---|---|
| `list_atomics` | `atomic-atlas list --json` | No |
| `read_atomic` | parser.load on a specific atomic path | No |
| `recon_target` | `atomic-atlas recon` | No |

`exec_atomic` over MCP is **deferred to v0.2**. It needs profile/auth handling (the agent must construct a target profile that the MCP server can read without leaking credentials — this is non-trivial).

## What the agent reasons about

The agent's value-add — what neither the CLI nor PyRIT alone can do:
- **Atomic selection.** Given recon output, picks the most informative atomic to run next (e.g., if recon detects RAG and tools, prefer T0051.001/rag_corpus over a direct_chat probe).
- **Backend adaptation.** When the CLI's adapter doesn't match the target's backend, the agent injects via the target's native API (Weaviate, Pinecone, custom HTTP) and records the manual step.
- **Payload variants.** Adapts seed payloads to observed target context (tool names, model family, system prompt fragments), writes the variant to `payloads/`, and re-runs via the CLI.
- **Semantic evaluation.** When `SubStringScorer` is too weak, applies the `## Success criteria` prose itself against the response transcript.
- **Chaining.** Recognizes when one atomic's success enables another (T0051.001 → T0053 → T0086) and runs the chain.

## Status

- [x] Claude Code skill: `skill/atomic-atlas.md` (rewritten to call the CLI)
- [x] CLI primitives the agent depends on: `list`, `recon`, `exec`, `report`, `validate`
- [x] PyRIT made optional so the MCP server can run without it
- [ ] MCP server: `mcp/server.py` (v0.1 scope: list_atomics, read_atomic, recon_target)
- [ ] MCP server: `exec_atomic` tool (v0.2 — needs profile/auth handling over MCP)
- [ ] Hermes agent profile / system prompt (v0.2)
