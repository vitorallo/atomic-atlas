# atomic-atlas — Product Requirements Document

**Version**: 0.4 (pre-release)
**Date**: 2026-05-17
**Author**: Vito Rallo, Cybersecurity Consult Partner · Benelux · Kyndryl
**Status**: Active development
**Companions**: [`SPEC.md`](SPEC.md) (atomic format), [`README.md`](README.md) (install + quickstart)

---

## Thesis

MITRE ATT&CK had a rich taxonomy and almost no runnable test coverage until Red Canary shipped **Atomic Red Team** in 2017 — small, technique-keyed, executable tests that turned "we detect T1059" from a claim into something you could fire and measure. MITRE **ATLAS** (the AI/agentic equivalent) is in exactly the pre-2017 position today: 170 techniques, 57 case studies, and no public, runnable, technique-keyed adversarial tests.

**atomic-atlas is Atomic Red Team for ATLAS** — an open, community-built library of technique-keyed, *delivery-vector-aware* atomic tests, backed by Microsoft PyRIT for orchestration and paired with an agent that adapts each abstract technique into a payload that actually lands on a specific target.

---

## Problem

Every "ATLAS-aligned" security claim today is **unfalsifiable**. A team that says "we cover indirect prompt injection (AML.T0051.001)" has no mechanical way to prove it. Three concrete gaps cause this.

### Problem 1 — Coverage is tactic-mapped, not technique-keyed

The most-cited ATLAS-aligned open-source tool, **Promptfoo** (now part of OpenAI), exposes ATLAS as a **tactic-level preset**: its adversarial-input plugins/strategies *generate* tests per target that roll up to ATLAS tactics, with untouched tactics — including the AI-native **AI Model Access** — left as explicit coverage gaps. Its docs cite a handful of technique IDs illustratively, but there is no contributor-curated, technique-keyed *atomic* catalog and no model of *how the attack is delivered*. Tactic mapping answers "are we roughly in this area"; it cannot answer "does AML.T0083 work against *this* agent, delivered via RAG vs MCP vs tool-response." We want the latter.

*(Sources: Promptfoo `mitre:atlas` docs + `working/promptfoo` checkout, retrieved 2026-05-17.)*

### Problem 2 — Same technique, different door

Existing tooling (PyRIT, garak, Promptfoo) tests LLMs well over **one** channel: the HTTP chat endpoint. Agentic systems expose **12 distinct entry vectors**: `direct_chat`, `system_prompt`, `rag_corpus`, `document_upload`, `tool_response`, `mcp_server`, `web_fetch`, `webhook`, `email`, `a2a_message`, `computer_use`, `model_api`. The *same* technique delivered through a poisoned RAG document is a different attack from the same technique typed into chat. Coverage is therefore a **2-D matrix (technique × vector)**, and a test must exist per *cell*, not per technique alone.

### Problem 3 — Techniques are abstract; payloads are target-specific

A technique definition is universal; the wording that triggers it is not. A jailbreak that extracts credentials from DVAA's LegacyBot does not land on a travel-agency chatbot. Static payload strings rot on contact with a real target. The fix is to treat the atomic as **intent** and let an LLM adapt the concrete payload to the specific target — "an agent that tests an agent."

### Why this matters now

ATLAS v5.6.0 (published 2026-05-04) flags **29 techniques as high-confidence agentic** (51 including probable) out of 170. atomic-atlas currently has runnable atomics for **12 of those 29 (41%)**. The taxonomy is racing ahead of any executable coverage — exactly the ATT&CK situation, pre-2017.

---

## Goal

Ship an open-source, community-built library of **technique-keyed, vector-aware atomic adversarial tests for MITRE ATLAS**, with two interchangeable runners over a shared catalog:

1. a **CLI** (`recon → list → adapt → exec → report`) backed by PyRIT, and
2. an **agentic skill** (an LLM agent that reads atomic intent, inspects the target, and reasons about delivery for vectors with no hard-coded adapter).

The flagship demo must run **`recon → exec → report` end-to-end against a local DVAA instance in under 60 seconds**, producing a verdict-shaped finding with captured evidence.

---

## Non-goals

- **Not a standalone LLM red-team tool.** PyRIT, garak, and Promptfoo do HTTP/chat-endpoint testing well; we extend, not replace.
- **Not a SaaS or commercial product.** Community library, MIT-licensed. Not a vendor, not a product.
- **Not a comprehensive ATLAS catalog at v0.x.** Breadth grows by community contribution; the format is deliberately easy enough to author a new cell in under an hour.
- **Not primarily a detection-engineering tool.** atomic-atlas is offensive (red-team). Verifying blue-team detection coverage is a valuable side effect, not the design center.

---

## Users

| User | Need |
|---|---|
| **AI red-teamer** | Reproducible ATLAS-keyed tests against a target agent; an engagement report a client will read |
| **Security engineer / SOC** | Verify a deployed agent holds under known ATLAS attacks; produce an ATLAS Navigator coverage layer |
| **Researcher / keynote speaker** | Demonstrate the agentic coverage gap concretely, then show the fix live |
| **Community contributor** | Add a `(technique × vector)` atomic in under an hour, with `validate` as the only gate |

---

## How it works (architecture essence)

- **The filesystem is the schema.** One markdown file per `(technique × vector)` cell — path `atomics/<ATLAS-id>/<vector>.md` encodes both dimensions. ~5 lines of YAML frontmatter + a prose body (Why this matters, Prerequisites, Attack strategy, Interaction, Success criteria, ATLAS mitigations, Cleanup). No registry, no plugin loader. The format is **AI-generatable**: an LLM given `SPEC.md` writes a valid atomic unaided.
- **Intent over implementation.** The atomic says *what* the attack does and *how to recognize success* in plain prose. The runner figures out *how* to execute it against the specific target.
- **PyRIT under the hood, optional at install.** atomic-atlas contributes new PyRIT `PromptTarget` subclasses for agentic vectors and uses `RedTeamingAttack`/`AttackAdversarialConfig` for multi-turn mutation. PyRIT is an **optional extra** (`[orchestrator]`) — `list`/`recon`/`report`/`validate`/MCP server run without it.
- **LLM where it matters.** `adapt` tunes the seed payload to the target (consuming atomic intent + `target_context` + recon JSON + prior evidence). A **two-tier scorer** (LLM judge → deterministic indicators fallback) produces a binary verdict *and* first-class structured **Evidence** (`tier`, `judge_reasoning`, `matched_indicators`, `extracted`, `duration_ms`).
- **Evidence is the finding.** `exec` and `runbook exec` append timestamped JSONL into a per-engagement directory. `report --format findings` aggregates by `(atomic, target)` into a stakeholder-facing markdown: verdict (`VULNERABLE` / `PARTIALLY_VULNERABLE` / `NOT_VULNERABLE` / `INCONCLUSIVE`) + severity + summary + extracted artifacts + ATLAS mitigations.
- **Runbooks are first-class.** Ordered atomic chains (kill chains) with `on_failure` policies (stop / continue / retry).
- **Runs, not pass/fail.** Every atomic reports a success rate over N runs — LLMs are non-deterministic and coverage claims must reflect that.
- **Authorization is mandatory; credentials never in atomics.** `--authorized` per exec; secrets only in target profiles via `${ENV}` references.

---

## Requirements

### R1 — Atomic format (MUST)
One `.md` per `(technique × vector)`. YAML frontmatter (technique ID, display name, vector, GUID, runs, `target_requires`, `multi_turn`, `success_indicators`, `judge_*`, `extractors`, `scoring`) validated by JSON Schema in CI. AI-generatable from `SPEC.md` alone.

### R2 — Entry-vector taxonomy (MUST)
The **12** canonical vectors enumerated in `SPEC.md`. Coverage is the technique × vector matrix; a cell with no atomic is an explicit gap, not an implicit pass.

### R3 — PyRIT integration (MUST)
atomic-atlas is a PyRIT extension, not a standalone orchestrator. PyRIT handles payload generation and multi-turn orchestration; atomic-atlas contributes agentic `PromptTarget` subclasses. PyRIT optional at install (`[orchestrator]` extra).

### R4 — Agentic targets (MUST)
`RAGCorpusTarget` (ChromaDB / Azure AI Search / HTTP ingest), `MCPServerTarget` (`http_registry_stub` + real `mcp_jsonrpc`), `ToolResponseTarget`, `DocumentUploadTarget`, `WebhookTarget` (port-0 callback), `DirectChatTarget` (wraps PyRIT `OpenAIChatTarget`). Each sets up, triggers, and cleans up.

### R5 — CLI (MUST)
`recon --target <url>` · `list` · `adapt <tech/vector> --target …` · `exec <tech/vector> --target … --authorized` · `report --engagement <dir> --format navigator|coverage|markdown|findings` · `validate [path]` · `runbook`.

### R6 — Payload adaptation (MUST)
`adapt` emits a domain-tuned bundle (rationale + payload + suggested observations + suggested indicators) from atomic intent, `target_context`, recon JSON, and prior evidence. Clean handoff to `exec --payload-file`. Audit trail via `generator_prompt_hash`.

### R7 — Scoring + Evidence (MUST)
Two-tier scorer (judge > indicators). Every scored run emits a first-class `Evidence` record. No silent downgrade — the tier used is recorded.

### R8 — Engagement memory + Findings (MUST)
Append-only JSONL per engagement dir (default `./atomic-atlas-engagement/`; override `--engagement` / `ATOMIC_ATLAS_ENGAGEMENT_DIR`). `report --format findings` aggregates to verdict + severity (5 levels, optional `severity_floor`) + summary + artifacts + mitigations. Filters `--target`, `--since`. No new LLM call.

### R9 — ATLAS Navigator output (MUST)
`report --format navigator` emits a valid Navigator layer, colour-coded by success rate; zero-atomic cells left uncoloured (the gap stays visible).

### R10 — Agentic skill / agent runner (SHOULD)
A skill reads atomic intent, inspects the target, and reasons about delivery for vectors with no hard-coded adapter (custom MCP, Weaviate RAG, …), evaluating success semantically against the `## Success criteria` prose. Claude Code skill today; generic-agent skill next.

### R11 — Authorization + authentication (MUST)
`--authorized` per exec; skill confirms authorization before executing. Credentials only in target profiles via `${ENV}`; Azure `DefaultAzureCredential` supported.

### R12 — Contribution path (SHOULD)
`_TEMPLATE/` for new contributors; `validate` is the CI gate; auto-generated catalog index; `atomics/unclassified/<slug>/` convention for atomics with no current ATLAS technique.

---

## Milestones

### v0.1 — Keynote-ready (shipped)
- [x] Atomic format + JSON Schema validation (`AML.TXXXX` and `UNCLASSIFIED.<slug>`)
- [x] `RAGCorpusTarget`, `MCPServerTarget` (stub + real JSON-RPC 2.0), `ToolResponseTarget`, `DocumentUploadTarget`, `WebhookTarget`, `DirectChatTarget`
- [x] CLI: `recon` / `exec` / `report` / `validate` / `list` / `runbook`
- [x] ATLAS Navigator + coverage-matrix reporters
- [x] Claude Code skill (CLI-driven); read-only MCP server (`atomic-atlas-mcp`)
- [x] Runbooks first-class; **22 DVAA runbooks** covering the full DVAA v0.8.0 catalog
- [x] `--hitl`, `target_context`, `RedTeamingAttack` integration, PyRIT 0.13 migration, PyRIT optional
- [x] ATLAS **v5.6.0** vendored at `data/atlas/`; `atomics/unclassified/` convention
- [ ] Initial git tag `v0.1.0`; full keynote rehearsal (architecture verified live against DVAA)

### v0.2 — Scoring, adaptation, engagement memory (shipped)
- [x] `success_indicators` + **LLM judge scorer** — two-tier stack + first-class `Evidence`; live-verified against DVAA (real LegacyBot creds extracted end-to-end). See [`docs/scoring.md`](docs/scoring.md).
- [x] **LLM-driven `adapt`** + `exec --payload-file` handoff; live-verified against DVAA-LegacyBot (2/2 in 15.8s). See [`docs/adapt.md`](docs/adapt.md).
- [x] **Engagement memory + Finding model + `report --format findings`** (commit `4c5421d`); post-merge simplification pass (`_resolve_target_id`, `asdict`, flattened `aggregate`).
- [ ] `A2ATarget` (unblocks `RB-DVAA-L4-02`; 3 `a2a_message` atomics already shipped)
- [ ] Canonical kill-chain runbooks (`indirect-pi-to-tool-exfil`, `rag-poison-to-cred-harvest`, `mcp-tool-poison-to-c2`) + engagement-template runbooks
- [ ] Catalog expansion toward the remaining high-confidence agentic techniques
- [ ] Cost estimation before exec; `last_verified_date` + model-drift CI; `runbook report` formats

### v0.3 — Community pipeline
- [ ] GitHub Actions CI (validate all atomics + runbooks on PR); auto-generated index + coverage badge
- [ ] PyPI release; Pinecone adapter; sibling vulnerable-agent examples (OpenAI Agents SDK, Anthropic SDK)
- [ ] `HITLTargetWrapper` auto-confirm threshold; `TelegramChatTarget` + `DiscordChatTarget`

### v0.4 — The agent that tests the agent
- [ ] `WebFetchTarget`, `EmailTarget`, `ComputerUseTarget` (12/12 canonical vectors)
- [ ] Generic-agent skill (beyond Claude Code) — the autonomous picker that reads recon, chooses techniques, adapts payloads, and reasons about novel delivery
- [ ] Blue-agent guardrail mode; streaming evidence; parallel runs
- [ ] Lobster — vulnerable LangGraph agent at `examples/lobster/`, ATLAS-tagged in source

---

## Success metrics

| Metric | Target | Actual (2026-05-17, repo-derived) |
|---|---|---|
| Seed atomics | ≥ 12 | **36** (2 unclassified) |
| Distinct ATLAS techniques with an atomic | ≥ 9 | **19** |
| High-confidence agentic coverage | n/a | **12 / 29 (41%)** · 15/51 incl. probable |
| Canonical entry vectors with ≥ 1 atomic | ≥ 5 | **7 / 12** |
| Frontmatter validation failures | 0 | **0** (27 atomics + 22 runbooks) |
| Test suite | 100% | **165 passed, 1 skipped** |
| DVAA challenges mapped to runbooks | n/a | **22 / 22** |
| ATLAS tactics traversed by runbooks | n/a | **9 / 16** |
| Flagship demo (`recon → exec → report`) | works vs DVAA | architecture verified live; full keynote rehearsal TODO |
| README time-to-first-test | < 5 min | < 5 min via `docs/quickstart.md` |

*ATLAS framework totals (v5.6.0, `data/atlas/MANIFEST.md`): 16 tactics (2 AI-native), 170 techniques incl. sub-techniques (101 top-level), 57 case studies, published 2026-05-04.*

---

## Open questions

1. **PyPI name** — `atomic-atlas` available; confirm before v0.3.
2. **MITRE coordination** — notify the ATLAS team once v0.1 is public, could strengthen legitimacy and drive Arsenal collaboration. This should happen in May 2026.
3. **DVAA dependency** — DVAA must expose a ChromaDB-compatible RAG endpoint for the flagship demo to include this use case (TO CONFIRM)
4. **MCP tool-registry format** — no standard yet for registering tools to an MCP server over HTTP; `MCPServerTarget` uses a placeholder pending a real implementation.
5. **Agentic-set definition** — adopt `29 high-confidence` as the canonical coverage denominator (vs `51` incl. probable)? The deck and PRD now both use 29; we confirmed these numbers by grepping over the project but we didn't run a manual 1-to-1 verfication, so still consider numbers an approximation and the need to confirm.
6. **Positioning vs an OpenAI-owned Promptfoo** — Promptfoo is now part of OpenAI and moving fast. This *strengthens* the case for an open, vendor-neutral, ATLAS-canonical commons rather than weakening it: the differentiator is the authored technique-keyed catalog + `technique × delivery-vector` matrix, not raw coverage breadth. Decide how explicitly to state "complementary, not competing" in public materials.
