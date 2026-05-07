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

## Current status

**128 tests passing, 1 skipped.** v0.1 is keynote-ready; v0.2 is in flight.

> **About DVAA in this repo.** Most examples target [DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent), a vulnerability simulator with scripted phrase-matched responses. It's the right harness to verify the runner mechanically, but it does not behave like a real LLM agent — single-shot LLM-generated payloads may not hit DVAA's narrow trigger set. For LLM-behavior validation, use Lobster (planned for v0.2; see [openspec/changes/vulnerable-agent](openspec/changes/vulnerable-agent)) or a real target you control.

### Across all OpenSpec changes

| Spec | Status | Notes |
|---|---|---|
| **atomic-format** | ✅ Shipped | Atomic markdown schema + parser. 27 atomics, 19 ATLAS techniques. |
| **agentic-targets** | ✅ Mostly shipped | 6 adapters live (`direct_chat`, `rag_corpus`, `mcp_server`, `tool_response`, `document_upload`, `webhook`). Missing: A2A, web_fetch, email, computer_use, model_api. |
| **agent-runner** | ✅ Shipped | Claude Code skill + MCP server (`atomic-atlas-mcp`). |
| **cli-and-reporting** | ✅ Shipped | `recon`, `list`, `validate`, `exec`, `report`, `runbook`, `adapt`. Reporters: navigator, coverage, markdown. |
| **runbooks** | ✅ Shipped | DAG executor + 22 DVAA runbooks. Missing: kill-chain runbooks, engagement templates. |
| **payload-adaptation** | ✅ Shipped | `target_context` profile field, `RedTeamingAttack` integration, `--hitl`. |
| **scoring-tiers** | ✅ Shipped (v0.2) | Three-tier scorer (judge → indicators → substring), first-class `Evidence`, regex extractors, refusal short-circuit. Live-verified end-to-end against DVAA. |
| **payload-adapter** | ✅ Shipped (v0.2) | `atomic-atlas adapt` CLI + `exec --payload-file` handoff. Bundle round-trip, observed-evidence selection. Live-verified end-to-end. |
| **atlas-agentic-coverage** | ⏳ Partial | Coverage tracking; updated as atomics are added. |
| **vulnerable-agent (Lobster)** | ❌ Not started | Custom vulnerable LangGraph agent. The DVAA phrase-matcher limit makes Lobster more valuable than originally scoped. |

### PRD milestones

- **v0.1 — Keynote-ready**: 14/16 ✅. Open: git tag `v0.1.0`, live keynote dry-run.
- **v0.2 — A2A, scoring, kill chains**: 2/9 done (scoring + adapter). Open: A2A target, web/email/computer-use targets, kill-chain runbooks, engagement runbooks, atomic catalog expansion (17 new ATLAS techniques), Lobster, cost telemetry, runbook reporters.
- **v0.3 — Community pipeline**: not started. CI, PyPI, sibling vulnerable agents.

### What's next — ranked by leverage

**Tier 1 — high leverage, demonstrably-relevant to the keynote:**

1. **Lobster (vulnerable-agent)** — real LLM target. DVAA is a phrase-matcher, not an LLM, so it can't truly evaluate adapter-generated payloads. A real LangGraph agent with ATLAS-tagged failures would prove the architecture against actual LLM behavior. ~1-2 days.
2. **Canonical kill-chain runbooks** under `runbooks/kill-chains/` — `indirect-pi-to-tool-exfil` (T0051.001 → T0053 → T0086), `rag-poison-to-cred-harvest`, `mcp-tool-poison-to-c2`. Strongest demo material for the keynote. ~half-day each.
3. **Live keynote dry-run** — rehearse the full deck against DVAA + Lobster end-to-end. The architecture is verified piece by piece but the talk pacing isn't.

**Tier 2 — fills demonstrable gaps:**

4. **A2ATarget** — unblocks `RB-DVAA-L4-02` (3 a2a_message atomics already shipped, no executor). Agent-to-agent attack story is one of the Five Dimensions. ~half-day.
5. **Backfill remaining 21 atomics with `success_indicators` / `judge_guidance`** — judge tier carries the load alone for most atomics today. ~1 day.

**Tier 3 — debt + polish:**

6. Tempfile leak fix in `_build_attack` RedTeamingAttack path (small, surgical).
7. `atomic-atlas init-profile` — CLI generator from recon output (operator UX).
8. Cost estimation before exec; `last_verified_date` field + model-drift CI.

**v0.2 simplification pass shipped this session** (commits `ac495c9` → `6d81421`):
- Archived 6 shipped OpenSpec changes; active spec dir down from 10 to 4.
- Single LLM factory (`src/atomic_atlas/llm.py`) replaces 3 duplicated chat-target setups.
- Frontmatter shrunk from 15 → 13 fields. Dropped `pyrit_orchestrator` + `pyrit_scorer` legacy class names; replaced with one `multi_turn` boolean.
- Dropped the unimplemented `composite` scorer strategy and the legacy `SubStringScorer` tier (now `judge` → `indicators`, two tiers).
- Refusal short-circuit collapsed from a 3-mode enum to a `scoring.refusal: bool`.
- Env vars consolidated: `ATOMIC_ATLAS_NO_ATTACKER_LLM` + `_SCORING` → `ATOMIC_ATLAS_OFFLINE`; `ATTACKER_MODEL` + `ADAPTER_MODEL` → `LLM_MODEL`.
- CLI down from 11 commands to 9 (`runbook show` removed; `runbook validate` merged into top-level `validate`, which now handles atomics + runbooks in one pass).

---

## Documentation

| Doc | What it covers |
|---|---|
| [docs/quickstart.md](docs/quickstart.md) | End-to-end: install, bring up DVAA, recon → exec → report; runbook exec; `--hitl` interactive review; `adapt` → `exec --payload-file` chain |
| [docs/use-cases.md](docs/use-cases.md) | Three end-to-end walkthroughs: smoke a single technique, chained kill chain with `adapt`, full engagement runbook |
| [docs/cli-reference.md](docs/cli-reference.md) | Per-subcommand reference: every flag with copy-pasteable examples |
| [docs/scoring.md](docs/scoring.md) | Scorer tiers (judge / indicators / substring), Evidence schema, `judge_guidance` / `judge_examples` / `extractors` authoring |
| [docs/adapt.md](docs/adapt.md) | Payload adapter: bundle format, prompt structure, observed-evidence selection rules, audit trail |
| [docs/install.md](docs/install.md) | Install matrix (`base` / `[orchestrator]` / `[mcp-server]`), why PyRIT is optional, troubleshooting |
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
