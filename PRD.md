# atomic-atlas — Product Requirements Document

**Version**: 0.1  
**Date**: 2026-05-06  
**Author**: Vito Rallo, Cybersecurity Consult Partner · Benelux · Kyndryl  
**Status**: Active development

---

## Problem

MITRE ATLAS has 167 techniques and 57 documented case studies. In the last 12 months, 21 new agent-specific techniques were added — MCP supply-chain attacks, agent-to-agent context poisoning, tool credential harvesting, resource exhaustion. None of these have public, runnable adversarial tests.

This means every "ATLAS-aligned" security product claim is **unfalsifiable**. A SOC team that says "we detect T0051.001 indirect prompt injection" has no mechanical way to verify it. The security community is in the same position ATT&CK was in before Red Canary shipped Atomic Red Team in 2017 — rich taxonomy, zero test coverage.

The specific gap is **agentic delivery vectors**. Existing tools (PyRIT, garak, Promptfoo) cover LLM testing via HTTP chat endpoints well. They do not cover how attacks arrive through the 11 other entry points that agentic systems expose: RAG corpus injection, MCP server poisoning, tool response interception, document upload pipelines, webhook-triggered agents, email, agent-to-agent messages, computer-use surfaces, and model API access.

---

## Goal

Ship an open-source, community-built library of technique-keyed, vector-aware atomic adversarial tests for MITRE ATLAS — backed by PyRIT for payload generation and orchestration, extended with new PyRIT targets for the agentic vectors that existing tools can't reach.

The first public version (v0.1) must be demoable live in a keynote setting: `recon → exec → report` in under 60 seconds against a local DVAA instance.

---

## Non-goals

- **Not a standalone LLM red-team tool.** PyRIT, garak, and Promptfoo already do HTTP/chat-endpoint testing. We don't re-implement what they do well.
- **Not a SaaS or commercial product.** Community library, MIT license.
- **Not a comprehensive ATLAS catalog.** v0.1 targets 9 techniques × focused agentic vectors. Breadth grows via community contribution.
- **Not a detection engineering tool.** atomic-atlas is offensive (red-team). Defensive use (verifying detection coverage) is a side effect, not the primary design goal.

---

## Users

| User | Need |
|---|---|
| **AI red-teamer** | Run reproducible ATLAS-keyed tests against a target agent; produce a coverage report for a client |
| **Security engineer / SOC** | Verify that a deployed agent behaves correctly under known ATLAS attacks; generate an ATLAS Navigator layer showing detection coverage |
| **Researcher / keynote speaker** | Demonstrate the agentic coverage gap concretely; have a live demo that shows the gap and the fix |
| **Community contributor** | Add a new (technique, vector) atomic to the library; know the format is simple enough to do in an hour |

---

## Requirements

### R1 — Atomic format (MUST)
- One `.md` file per `(ATLAS technique × entry vector)` cell
- YAML frontmatter: technique ID, vector, GUID, run count, PyRIT orchestrator, required target capabilities
- Markdown body: Why this matters, Prerequisites, Attack strategy, Interaction, Success criteria, ATLAS mitigations, Cleanup
- Frontmatter validated by JSON Schema in CI
- Format is AI-generatable: an LLM given the spec can write a new valid atomic without additional guidance

### R2 — Entry vector taxonomy (MUST)
- 12 named vectors covering all channels through which untrusted input can reach an agent
- Coverage is a 2D matrix: technique × vector; a test exists per cell, not per technique alone

### R3 — PyRIT integration (MUST)
- atomic-atlas is a PyRIT extension, not a standalone orchestrator
- PyRIT handles payload generation (RedTeamingOrchestrator) and multi-turn orchestration
- atomic-atlas contributes new PyRIT `PromptTarget` subclasses for agentic vectors

### R4 — Agentic targets (MUST)
- `RAGCorpusTarget`: inject payload into ChromaDB, Pinecone, Azure AI Search, or generic HTTP ingest; trigger retrieval; cleanup
- `MCPServerTarget`: register poisoned tool on MCP server; deregister on cleanup
- `ToolResponseTarget`: mock tool server serving a poisoned response; stop on cleanup
- `DocumentUploadTarget`: upload payload file; trigger processing; delete on cleanup
- `WebhookTarget`: POST crafted payload to agent inbound webhook

### R5 — CLI (MUST)
- `atomic-atlas recon --target <url>`: enumerate vectors, fingerprint guardrails, suggest techniques
- `atomic-atlas exec <technique/vector> --target <url> --authorized`: run atomic via PyRIT
- `atomic-atlas report --input results.json --format navigator|coverage|markdown`
- `atomic-atlas validate [path]`: check frontmatter schema

### R6 — ATLAS Navigator output (MUST)
- `report --format navigator` produces a valid Navigator layer JSON
- Color-coded by success rate; cells with zero atomics are left uncolored

### R7 — Agent runner / Claude Code skill (SHOULD)
- Skill reads atomic intent, inspects target, reasons about delivery for novel implementations
- Handles vectors with no hard-coded adapter (Weaviate RAG, custom MCP, etc.)
- Evaluates success semantically against `## Success criteria` prose

### R8 — Authorization gate (MUST)
- CLI requires `--authorized` flag per exec run
- Skill asks user to confirm authorization before executing
- No test executes without explicit confirmation

### R9 — Authentication (MUST)
- Credentials live in target profiles only; never in atomic files
- Env var references (`${VAR_NAME}`) in all profile credential fields
- Azure DefaultAzureCredential supported for Azure AI Search and Azure OpenAI targets

### R10 — Contribution path (SHOULD)
- `_TEMPLATE/vector_template.md` for new contributors
- `atomic-atlas validate` is the CI gate for PRs
- `index.yaml` catalog auto-generated from the atomics directory

---

## Milestones

### v0.1 — Keynote-ready (shipped)
- [x] **27 atomics** across 19 ATLAS-real techniques + 1 unclassified slug (was 12 → expanded during the DVAA harvest)
- [x] JSON Schema frontmatter validation (accepts AML.TXXXX and UNCLASSIFIED.<slug>)
- [x] **RAGCorpusTarget** (ChromaDB + Azure AI Search + HTTP ingest)
- [x] **MCPServerTarget** with two modes: `http_registry_stub` placeholder and `mcp_jsonrpc` real JSON-RPC 2.0
- [x] **ToolResponseTarget**, **DocumentUploadTarget**, **WebhookTarget** (port-0 callback)
- [x] **DirectChatTarget** wrapping PyRIT's OpenAIChatTarget — closed the `direct_chat` UnsupportedVector gap
- [x] **CLI: recon / exec / report / validate / list / runbook**
- [x] ATLAS Navigator reporter, coverage matrix reporter
- [x] Claude Code skill (CLI-driven)
- [x] **MCP server** (`atomic-atlas-mcp`) — read-only tools `list_atomics` / `read_atomic` / `recon_target`, no PyRIT required
- [x] **Runbooks as a first-class concept** — ordered atomic chains with on_failure policies (stop / continue / retry); 22 DVAA runbooks shipped covering the entire DVAA v0.8.0 catalog
- [x] **`--hitl` flag** on `exec` and `runbook exec` for interactive operator confirmation per outbound send
- [x] **`target_context`** profile field flowing into the attacker LLM's system prompt for domain-aware payload adaptation
- [x] **`RedTeamingAttack` proper integration** with `AttackAdversarialConfig` so `RedTeamingOrchestrator`-tagged atomics actually drive multi-turn mutation
- [x] PyRIT 0.13 API migration (orchestrators → attacks)
- [x] PyRIT as **optional dependency** (`[orchestrator]` extra) so list / recon / report / validate / MCP server work in lightweight installs
- [x] **ATLAS v5.6.0 framework data vendored** at `data/atlas/`
- [x] **`atomics/unclassified/` convention** for atomics with no current ATLAS technique
- [x] SPEC.md, PRD.md, runbooks/README.md, docs/quickstart.md, docs/install.md, docs/targets.md, docs/agent-runner.md, docs/atlas-coverage.md
- [ ] Initial git tag `v0.1.0`
- [ ] Live keynote dry-run (architecture verified end-to-end against DVAA; full keynote rehearsal still TODO)

### v0.2 — A2A, scoring, kill chains
- [ ] **A2ATarget** — unblocks live exec for `RB-DVAA-L4-02` (3 a2a_message atomics already shipped)
- [ ] **WebFetchTarget**, **EmailTarget**, **ComputerUseTarget**
- [x] **`success_indicators` frontmatter field** + **LLM judge scorer** — three-tier scorer stack (judge > indicators > legacy substring) plus first-class `Evidence` (`tier`, `judge_reasoning`, `matched_indicators`, `extracted`, `duration_ms`). Live-verified against DVAA: judge tier extracts real LegacyBot creds (`sk-dvaa-openai-test-key-…`, `dvaa-admin-secret`) end-to-end. See [`docs/scoring.md`](docs/scoring.md). [openspec/changes/scoring-tiers]
- [x] **LLM-driven payload generator** (`atomic-atlas adapt`) + **clean handoff to exec** (`exec --payload-file`). Generator consumes the atomic's intent, target_context, recon JSON, and prior `results.json` evidence to emit a domain-tuned payload bundle (rationale + payload + suggested observations + suggested indicators). Audit trail via `generator_prompt_hash`. Live-verified end-to-end against DVAA-LegacyBot (2/2 success in 15.8s). See [`docs/adapt.md`](docs/adapt.md). [openspec/changes/payload-adapter]
- [x] **Engagement memory + Finding model + `report --format findings`**. `exec` and `runbook exec` accumulate timestamped JSONL into a per-engagement directory (default `./atomic-atlas-engagement/`, override via `--engagement` or `ATOMIC_ATLAS_ENGAGEMENT_DIR`). `report --format findings` aggregates by `(atomic, target)`, emits a stakeholder-facing markdown — verdict (`VULNERABLE` / `PARTIALLY_VULNERABLE` / `NOT_VULNERABLE` / `INCONCLUSIVE`) + severity (5 levels, with optional `severity_floor` frontmatter) + summary (strongest judge_reasoning) + extracted artifacts + ATLAS mitigations parsed from atomic body. Filters: `--target`, `--since`. No new LLM call. 37 new tests; live-verified end-to-end. [commit `4c5421d`]
- [ ] **Canonical kill-chain runbooks** under `runbooks/kill-chains/`: `indirect-pi-to-tool-exfil` (T0051.001 → T0053 → T0086), `rag-poison-to-cred-harvest`, `mcp-tool-poison-to-c2`
- [ ] **Engagement-template runbooks** under `runbooks/engagement/`
- [ ] Atomic catalog expansion: 17 new ATLAS-v5.6.0 agentic techniques (T0070, T0071, T0080.x, T0081, T0082, T0083, T0084.x, T0085.x, T0103, T0108, T0112.000)
- [ ] Lobster — vulnerable LangGraph agent shipped at `examples/lobster/`, ATLAS-tagged in source
- [ ] Cost estimation before exec; `last_verified_date` field + model-drift CI
- [ ] `runbook report --format navigator|markdown|kill-chain`

### v0.3 — Community contribution pipeline
- [ ] GitHub Actions CI: validate all atomics + runbooks on PR
- [ ] Auto-generated index.yaml and coverage badge
- [ ] Pinecone adapter for RAGCorpusTarget
- [ ] PyPI release
- [ ] Sibling vulnerable-agent examples (OpenAI Agents SDK, Anthropic SDK)
- [ ] **`HITLTargetWrapper`** auto-confirm threshold (`--hitl-threshold N`)
- [ ] **TelegramChatTarget** + **DiscordChatTarget** (real-world deployment surfaces)

---

## Success metrics

| Metric | v0.1 target | v0.1 actual |
|---|---|---|
| Seed atomics | ≥ 12 | **27** |
| ATLAS techniques covered | ≥ 9 | **19** + 1 unclassified slug |
| Entry vectors with at least one atomic | ≥ 5 | **7** |
| Parser test pass rate | 100% | **100%** (49/49 + 1 skipped) |
| Frontmatter validation: zero failures | 100% | **100%** (27 atomics + 22 runbooks) |
| ATLAS v5.6.0 high-confidence agentic technique coverage | n/a | **19 / 29 (66%)** |
| ATLAS tactics traversed by runbooks | n/a | **9 of 16** |
| DVAA challenges mapped to runbooks | n/a | **22 / 22** |
| Keynote demo end-to-end (recon → exec → navigator) | Working against DVAA | Architecture verified live; full keynote rehearsal TODO |
| README time-to-first-test | < 5 minutes for a practitioner with Python and DVAA | < 5 min via docs/quickstart.md |

---

## Open questions

1. **PyPI name**: `atomic-atlas` is available; confirm before v0.3 release.
2. **MITRE coordination**: Worth notifying MITRE ATLAS team once v0.1 is public? Would strengthen legitimacy and potentially drive Arsenal collaboration.
3. **DVAA dependency**: DVAA (opena2a-org) must expose a ChromaDB-compatible RAG endpoint for the flagship demo. Confirm this before the keynote.
4. **MCP tool registry format**: No standard yet for registering tools to an MCP server via HTTP. The MCPServerTarget currently uses a placeholder; needs real MCP server implementation target.
