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

## 60-second snapshot

```bash
# Full install (Python 3.10–3.13). PyRIT is in [orchestrator] — opt-in;
# the base install is enough for list / recon / report / validate / MCP.
pip install 'atomic-atlas[orchestrator]'

atomic-atlas list                                              # browse the catalog
atomic-atlas recon --target http://localhost:8080              # fingerprint a target
atomic-atlas exec AML.T0051.001/rag_corpus \
  --target http://localhost:8080 \
  --profile targets/dvaa_local.yaml \
  --authorized                                                 # run the flagship atomic
atomic-atlas report --input results.json --format navigator    # ATLAS Navigator layer JSON
```

> **Authorization required.** Running these tests against systems you do not own or have written permission to test is unethical and likely illegal. The `--authorized` flag is your confirmation.

For the full walkthrough — installing, bringing up [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent), running the demo end-to-end, opening the result in ATLAS Navigator — see **[docs/quickstart.md](docs/quickstart.md)**.

---

## Documentation

| Doc | What it covers |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | End-to-end: install, bring up DVAA, recon → exec → report |
| [docs/install.md](docs/install.md) | Install matrix (`base` / `[orchestrator]` / `[mcp-server]`), why PyRIT is optional, troubleshooting |
| [docs/targets.md](docs/targets.md) | Target profile format, DVAA setup, Lakera Gandalf alternative, auth schemes |
| [docs/agent-runner.md](docs/agent-runner.md) | Claude Code skill + MCP server, when to use them vs the CLI |
| [SPEC.md](SPEC.md) | Atomic format reference (frontmatter, body sections, vectors, payloads) |
| [PRD.md](PRD.md) | Product requirements + milestone scope |

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

A layer **above** the CLI. The CLI is the deterministic primitive; the agent reasons about which atomic to run, adapts payloads to the observed target, evaluates success semantically, and chains atomics. Two implementations, one contract:

- **Claude Code skill** — `/atomic-atlas exec AML.T0051.001/rag_corpus --target http://custom-agent.local`
- **MCP server** — `pip install 'atomic-atlas[mcp-server]' && atomic-atlas-mcp` for Hermes, GPT-4o, Gemini, AutoGen, LangChain, and any other MCP-capable agent.

See **[docs/agent-runner.md](docs/agent-runner.md)** for the full surface, fallback rules, and MCP client config.

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
