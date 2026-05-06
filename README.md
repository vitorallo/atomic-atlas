# atomic-atlas

**ATLAS-keyed agentic security tests. The Atomic Red Team for AI agents.**

---

MITRE ATLAS has 167 techniques and 57 case studies. The most important ones — the 21 agent-specific techniques added in the last 12 months — have zero public runnable tests.

Without runnable tests, every "ATLAS-aligned" product claim is unverifiable. Vendors and security teams alike say "we cover X" with no mechanical way to check. This is the same failure mode ATT&CK had before Atomic Red Team in 2017.

atomic-atlas fills that gap.

---

## What it is

A library of small, self-contained adversarial tests, each mapped to an ATLAS technique ID and an entry vector. Backed by [PyRIT](https://github.com/Azure/PyRIT) for payload generation and attack orchestration. Adds what PyRIT doesn't have: agentic delivery targets for the 11 non-chat entry vectors (RAG injection, MCP tool poisoning, tool response interception, document upload, webhook, email, A2A, computer-use).

The format is Markdown with YAML frontmatter — one `.md` file per `(technique × vector)` cell. File path encodes both dimensions:

```
atomics/AML.T0051.001/rag_corpus.md   ← technique + vector
```

**Traditional HTTP chat testing is not the goal.** PyRIT, garak, and Promptfoo already do that well. This project exists for the delivery vectors they don't cover.

---

## Quick start

```bash
# Lightweight install — list, recon, report, validate, MCP server.
# Right for atomic authors and the agent-runner MCP layer.
pip install atomic-atlas

# Full install — adds PyRIT and unlocks `exec`. Pulls in PyRIT's transitive
# deps (azure-ai, openai, anthropic, chromadb, etc.). Required for keynote
# demo and any actual atomic execution.
pip install 'atomic-atlas[orchestrator]'

# Enumerate atomics in the catalog (no PyRIT needed)
atomic-atlas list
atomic-atlas list --vector rag_corpus --json

# Enumerate which vectors your target exposes (no PyRIT needed)
atomic-atlas recon --target http://dvaa.local

# Run a specific atomic (PyRIT required; --authorized confirms permission)
atomic-atlas exec AML.T0051.001/rag_corpus \
  --target http://dvaa.local \
  --profile targets/dvaa_local.yaml \
  --authorized

# Generate ATLAS Navigator layer from results
atomic-atlas report --input results.json --format navigator --output layer.json

# Show coverage matrix
atomic-atlas report --input results.json --format coverage
```

> **Authorization required.** Running these tests against systems you do not own or have written permission to test is unethical and likely illegal. The `--authorized` flag is your confirmation.

---

## Entry vectors

| Vector | Description |
|---|---|
| `direct_chat` | User message to the chat interface |
| `rag_corpus` | Document injected into the retrieval corpus |
| `document_upload` | File submitted directly to the agent |
| `tool_response` | Poisoned response returned by a tool |
| `mcp_server` | Tool registered on an MCP server |
| `web_fetch` | Content on a webpage the agent browses |
| `webhook` | Payload delivered via inbound webhook |
| `email` | Email body/attachment triggering agent processing |
| `a2a_message` | Agent-to-agent message |
| `computer_use` | Content injected into a screen the agent sees |
| `model_api` | Direct model API interaction |

The same ATLAS technique entering through different vectors is a different attack, with different defenses and different payloads. Coverage is a 2D matrix of `technique × vector`, not a flat list.

---

## Agent runner

The agent runner is a layer **above** the CLI. The CLI is the deterministic primitive; the agent reasons about which atomic to run, adapts payloads to the observed target, evaluates success semantically, and chains atomics into a kill chain. The agent only bypasses the CLI when no adapter exists for the vector or for the target's specific backend.

Two implementations, one contract:

### Claude Code skill (`skill/atomic-atlas.md`)

```
/atomic-atlas exec AML.T0051.001/rag_corpus --target http://custom-agent.local
```

The skill calls `atomic-atlas list / recon / exec / report` as its primary path; manual delivery (raw HTTP, custom Python) is the documented fallback for vectors with no CLI adapter.

### MCP server (`atomic-atlas-mcp`)

For Hermes, GPT-4o, Gemini, AutoGen, LangChain, and any other MCP-capable agent.

```bash
pip install 'atomic-atlas[mcp-server]'
atomic-atlas-mcp                       # stdio MCP server
```

Exposes three read-only tools (no PyRIT required):
- `list_atomics(vector?, technique?)` — catalog discovery
- `read_atomic(path)` — full atomic content
- `recon_target(target, auth_header?)` — vector fingerprinting

`exec_atomic` over MCP is deferred to v0.2 (needs profile/auth transport design).

---

## Seed atomics (v0.1)

| Technique | Vector(s) |
|---|---|
| AML.T0051.000 Direct Prompt Injection | `direct_chat` |
| AML.T0051.001 Indirect Prompt Injection | `rag_corpus`, `document_upload`, `mcp_server`, `tool_response` |
| AML.T0053 Agent Tool Invocation | `tool_response` |
| AML.T0065 LLM Prompt Crafting | `direct_chat` |
| AML.T0086 Exfiltration via Agent Tool | `mcp_server` |
| AML.T0093 Prompt Infiltration via Public App | `webhook` |
| AML.T0098 Tool Credential Harvesting | `tool_response` |
| AML.T0099 Tool Data Poisoning | `tool_response` |
| AML.T0104 Publish Poisoned AI Agent Tool | `mcp_server` |

---

## Contribute an atomic

One PR = one atomic. The format is simple:

1. Pick a `(technique, vector)` cell not in the catalog (`atomic-atlas report --format coverage`)
2. Copy `atomics/_TEMPLATE/vector_template.md` and rename it
3. Fill in the frontmatter and body sections
4. Add any payload seed files to `payloads/`
5. Run `atomic-atlas validate` to check the frontmatter
6. Open a PR

See [SPEC.md](SPEC.md) for the full format specification.

---

## Not a product. Not a vendor.

This is a community library. Contributions framed as research or practitioner tooling, not as commercial offerings.

The goal: a coverage commons for AI security teams, so "ATLAS-aligned" becomes a claim you can verify.

---

## Related work

- [MITRE ATLAS](https://atlas.mitre.org) — the technique matrix
- [PyRIT](https://github.com/Azure/PyRIT) — the orchestration backbone this project extends
- [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent) — the recommended test target
- [MITRE Arsenal](https://github.com/mitre-atlas/arsenal) — predecessor (stale, no agentic coverage)
- [Promptfoo ATLAS plugin](https://www.promptfoo.dev/docs/red-team/mitre-atlas/) — 6/167 coverage, no entry-vector dimension
