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

### v0.1 — Keynote-ready (current)
- [ ] 12 seed atomics (9 techniques × focused agentic vectors)
- [ ] JSON Schema frontmatter validation
- [ ] RAGCorpusTarget (ChromaDB + Azure AI Search + HTTP ingest)
- [ ] MCPServerTarget
- [ ] ToolResponseTarget
- [ ] DocumentUploadTarget
- [ ] WebhookTarget
- [ ] CLI: recon / exec / report / validate
- [ ] ATLAS Navigator reporter
- [ ] Coverage matrix reporter
- [ ] Claude Code skill
- [ ] SPEC.md + PRD.md + OPENSPEC.md
- [ ] README with demo instructions
- [ ] Initial git tag `v0.1.0`

### v0.2 — Chain support + broader target coverage
- [ ] Atomic chaining: stitch T0051.001 → T0053 → T0086 into a kill chain
- [ ] A2ATarget (agent-to-agent message delivery)
- [ ] MCP server (expose library as MCP tools for any AI agent to use)
- [ ] More atomics: email, A2A, computer-use vectors
- [ ] Cost estimation before exec
- [ ] `last_verified_date` field + model drift CI

### v0.3 — Community contribution pipeline
- [ ] GitHub Actions CI: validate all atomics on PR
- [ ] Auto-generated index.yaml and coverage badge
- [ ] Pinecone adapter for RAGCorpusTarget
- [ ] LLM judge scorer (semantic success evaluation)
- [ ] PyPI release

---

## Success metrics

| Metric | v0.1 target |
|---|---|
| Seed atomics | ≥ 12 |
| ATLAS techniques covered | ≥ 9 |
| Entry vectors with at least one atomic | ≥ 5 |
| Parser test pass rate | 100% |
| Frontmatter validation: zero failures | 100% |
| Keynote demo end-to-end (recon → exec → navigator) | Working against DVAA |
| README time-to-first-test | < 5 minutes for a practitioner with Python and DVAA |

---

## Open questions

1. **PyPI name**: `atomic-atlas` is available; confirm before v0.3 release.
2. **MITRE coordination**: Worth notifying MITRE ATLAS team once v0.1 is public? Would strengthen legitimacy and potentially drive Arsenal collaboration.
3. **DVAA dependency**: DVAA (opena2a-org) must expose a ChromaDB-compatible RAG endpoint for the flagship demo. Confirm this before the keynote.
4. **MCP tool registry format**: No standard yet for registering tools to an MCP server via HTTP. The MCPServerTarget currently uses a placeholder; needs real MCP server implementation target.
