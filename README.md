# atomic-atlas

**ATLAS-keyed agentic security tests. The Atomic Red Team for AI agents.**

---

MITRE ATLAS v5.6.0 has 170 techniques and 57 case studies. The 29 high-confidence agentic techniques (51 including probable) have almost zero public runnable tests.

Without runnable tests, every "ATLAS-aligned" product claim is unverifiable. Vendors and security teams alike say "we cover X" with no mechanical way to check. This is the same failure mode ATT&CK had before Atomic Red Team in 2017.

atomic-atlas fills that gap.

---

## 📄 See a real assessment

**→ [Sample assessment, explained (PDF)](docs/sample_assessment1/sample_assessment_explained.pdf)** — a real, live engagement against DVAA LegacyBot, walked through end to end: what ran, why a multi-turn run takes minutes, and how to read the resulting **VULNERABLE / HIGH** finding with extracted credentials.

| | |
|---|---|
| 📄 **Explainer PDF** | [docs/sample_assessment1/sample_assessment_explained.pdf](docs/sample_assessment1/sample_assessment_explained.pdf) |
| 📝 **Step-by-step walkthrough** | [docs/sample_execution.md](docs/sample_execution.md) — every command + output |
| 📦 **Raw artifacts (committed verbatim)** | [docs/sample_assessment1/](docs/sample_assessment1/) — `results.jsonl`, findings / navigator / coverage / run reports, recon ([file map](docs/sample_assessment1/README.md)) |

Nothing in the sample is synthetic — it is the exact output of one `recon → exec → report` run.

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
                                                               # (appends to ./atomic-atlas-engagement/)
atomic-atlas report --format findings                          # stakeholder verdict + evidence
atomic-atlas report --format navigator                         # ATLAS Navigator layer JSON
```

> **Authorization required.** Running these tests against systems you do not own or have written permission to test is unethical and likely illegal. The `--authorized` flag is your confirmation.

For the full walkthrough — installing, bringing up [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent), running the demo end-to-end, opening the result in ATLAS Navigator — see **[docs/quickstart.md](docs/quickstart.md)**.

---

## Current status

**165 tests passing, 1 skipped.** v0.1 is keynote-ready; v0.2 is largely shipped.

> **About DVAA in this repo.** Most examples target [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent), a vulnerability simulator with scripted phrase-matched responses. It's the right harness to verify the runner mechanically, but it does not behave like a real LLM agent — single-shot LLM-generated payloads may not hit DVAA's narrow trigger set. For LLM-behavior validation, use Lobster (planned for v0.4; see [openspec/changes/vulnerable-agent](openspec/changes/vulnerable-agent)) or a real target you control.

### Across all OpenSpec changes

| Spec | Status | Notes |
|---|---|---|
| **atomic-format** | ✅ Shipped | Atomic markdown schema + parser. 36 atomics, 19 ATLAS techniques (12/29 high-confidence agentic). |
| **agentic-targets** | ✅ Mostly shipped | 6 adapters live (`direct_chat`, `rag_corpus`, `mcp_server`, `tool_response`, `document_upload`, `webhook`). Missing: A2A, web_fetch, email, computer_use, model_api. |
| **agent-runner** | ✅ Shipped | Claude Code skill + MCP server (`atomic-atlas-mcp`). |
| **cli-and-reporting** | ✅ Shipped | `recon`, `list`, `validate`, `exec`, `report`, `runbook`, `adapt`. Reporters: navigator, coverage, markdown. |
| **runbooks** | ✅ Shipped | DAG executor + 22 DVAA runbooks. Missing: kill-chain runbooks, engagement templates. |
| **payload-adaptation** | ✅ Shipped | `target_context` profile field, `RedTeamingAttack` integration, `--hitl`. |
| **scoring-tiers** | ✅ Shipped (v0.2) | Two-tier scorer (judge → indicators), first-class `Evidence`, regex extractors, refusal short-circuit. Live-verified end-to-end against DVAA. |
| **payload-adapter** | ✅ Shipped (v0.2) | `atomic-atlas adapt` CLI + `exec --payload-file` handoff. Bundle round-trip, observed-evidence selection. Live-verified end-to-end. |
| **atlas-agentic-coverage** | ⏳ Partial | Coverage tracking; updated as atomics are added. |
| **vulnerable-agent (Lobster)** | ❌ Not started | Custom vulnerable LangGraph agent. The DVAA phrase-matcher limit makes Lobster more valuable than originally scoped. |

### PRD milestones

- **v0.1 — Keynote-ready**: 14/16 ✅. Open: git tag `v0.1.0`, live keynote dry-run.
- **v0.2 — Scoring, adaptation, engagement memory**: scoring tiers + `adapt` + engagement/Findings shipped. Open: A2A target, canonical kill-chain + engagement-template runbooks, catalog expansion toward the remaining high-confidence agentic techniques (12/29 covered), cost telemetry, runbook reporters.
- **v0.3 — Community pipeline**: not started. CI, PyPI, Pinecone adapter, sibling vulnerable agents.
- **v0.4 — The agent that tests the agent**: web/email/computer-use targets (12/12 vectors), generic-agent skill, Lobster vulnerable LangGraph agent.

### What's next — ranked by leverage

**Tier 1 — high leverage, demonstrably-relevant to the keynote:**

1. **Lobster (vulnerable-agent)** — real LLM target. DVAA is a phrase-matcher, not an LLM, so it can't truly evaluate adapter-generated payloads. A real LangGraph agent with ATLAS-tagged failures would prove the architecture against actual LLM behavior. ~1-2 days.
2. **Canonical kill-chain runbooks** under `runbooks/kill-chains/` — `indirect-pi-to-tool-exfil` (T0051.001 → T0053 → T0086), `rag-poison-to-cred-harvest`, `mcp-tool-poison-to-c2`. Strongest demo material for the keynote. ~half-day each.
3. **Live keynote dry-run** — rehearse the full deck against DVAA + Lobster end-to-end. The architecture is verified piece by piece but the talk pacing isn't.

**Tier 2 — fills demonstrable gaps:**

4. **A2ATarget** — unblocks `RB-DVAA-L4-02` (3 a2a_message atomics already shipped, no executor). Agent-to-agent attack story is one of the Five Dimensions. ~half-day.
5. **Backfill atomics that still rely on the judge tier alone with `success_indicators` / `judge_guidance`** — gives the indicator tier something to fall back to when no judge LLM is reachable. ~1 day.

**Tier 3 — debt + polish:**

6. Tempfile leak fix in `_build_attack` RedTeamingAttack path (small, surgical).
7. `atomic-atlas init-profile` — CLI generator from recon output (operator UX).
8. Cost estimation before exec; `last_verified_date` field + model-drift CI.

---

## Documentation

| Doc | What it covers |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | End-to-end: install, bring up DVAA, recon → exec → report; runbook exec; `--hitl` interactive review; `adapt` → `exec --payload-file` chain |
| [docs/sample_execution.md](docs/sample_execution.md) | Verbatim walkthrough of one real live run (DVAA LegacyBot, `AML.T0083`): every command + output, why multi-turn exec takes minutes, how to read the VULNERABLE/HIGH finding |
| [docs/use-cases.md](docs/use-cases.md) | Three end-to-end walkthroughs: smoke a single technique, chained kill chain with `adapt`, full engagement runbook |
| [docs/benchmarks.md](docs/benchmarks.md) | 12 live runs across 6 DVAA bots — same response, three judge verdicts; runtime as fitness signal; reproducible commands |
| [docs/cli-reference.md](docs/cli-reference.md) | Per-subcommand reference: every flag with copy-pasteable examples |
| [docs/scoring.md](docs/scoring.md) | Scorer tiers (judge / indicators), Evidence schema, `judge_guidance` / `judge_examples` / `extractors` authoring |
| [docs/sample_execution.md](docs/sample_execution.md) | Verbatim real end-to-end run (recon → exec → findings) against DVAA LegacyBot; committed artifacts in [docs/sample_assessment1/](docs/sample_assessment1/) |
| [docs/adapt.md](docs/adapt.md) | Payload adapter: bundle format, prompt structure, observed-evidence selection rules, audit trail |
| [docs/install.md](docs/install.md) | Install matrix (`base` / `[orchestrator]` / `[mcp-server]`), why PyRIT is optional, troubleshooting |
| [docs/pyrit.md](docs/pyrit.md) | How atomic-atlas uses PyRIT: why the dependency, exact symbols consumed (target/attack/scorer/memory), what we deliberately don't take, version caveat, the integration seam |
| [docs/targets.md](docs/targets.md) | Target profile format, `target_context` for domain-aware payload adaptation, DVAA setup, auth schemes |
| [docs/agent-runner.md](docs/agent-runner.md) | Claude Code skill + MCP server, when to use them vs the CLI |
| [docs/atlas-coverage.md](docs/atlas-coverage.md) | Project-wide ATLAS v5.6.0 coverage stats (techniques, vectors, tactics, runbooks) |
| [runbooks/dvaa/README.md](runbooks/dvaa/README.md) | DVAA → ATLAS mapping (22 challenges, side-by-side technique counts) |
| [SPEC.md](SPEC.md) | Atomic format reference; payload-adaptation principles |
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

## Seed atomics (original v0.1 priority set)

The 9 priority techniques the catalog started from. It has since grown to **36 atomics across 19 ATLAS techniques** — run `atomic-atlas report --format coverage` for the live matrix.

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
- [Promptfoo ATLAS plugin](https://www.promptfoo.dev/docs/red-team/mitre-atlas/) — tactic-level only: 39 generic plugins → 14/16 ATLAS tactics, 0/2 AI-native tactics, 0 techniques by ID; no entry-vector dimension
