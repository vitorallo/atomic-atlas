# Quick start

Goal of this doc: take you from a clean machine to a successful `recon → exec → report` cycle against a vulnerable AI agent in about ten minutes.

> Want to see the finished output *before* running anything? [`docs/sample_assessment1/sample_execution.md`](sample_assessment1/sample_execution.md) is this exact walkthrough captured verbatim against a live target, with every command and its real output.

## What you'll have at the end

- atomic-atlas installed locally
- A vulnerable AI agent ([DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent)) running locally — we use **LegacyBot on `localhost:7003`**
- A successful run of `AML.T0083/direct_chat` (Credentials from AI Agent Configuration)
- A stakeholder **findings report** + an **ATLAS Navigator layer** JSON you can paste into [the Navigator](https://mitre-atlas.github.io/atlas-navigator/)

## Prerequisites

- **Python 3.10–3.13** (PyRIT 0.13 does not support 3.14). Check with `python3 --version`.
- **Docker** for running DVAA locally.
- An **OpenAI API key** (or any OpenAI-compatible provider — OpenRouter, Ollama, vLLM, LiteLLM) for the attacker LLM that PyRIT's `RedTeamingAttack` uses and for the LLM judge. Configured in `.env` (Step 4).

If anything fails during install, see [docs/install.md](install.md) for the install matrix and common-error troubleshooting.

## Step 1 — install atomic-atlas

```bash
git clone https://github.com/<your-fork>/atomic-atlas.git
cd atomic-atlas
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[orchestrator]'    # base + PyRIT for `exec`
```

> **Why an extra?** PyRIT is heavy (~1 GB transitive) and only required for `atomic-atlas exec`. The base install is enough for `list / recon / report / validate` and for running the MCP server. See [docs/install.md](install.md) and [docs/pyrit.md](pyrit.md).

Sanity-check the install:

```bash
atomic-atlas --help
atomic-atlas list                    # should print 27 atomics
atomic-atlas validate                # should end: "All 49 file(s) valid (27 atomic, 22 runbook)."
```

## Step 2 — bring up DVAA

DVAA is an intentionally vulnerable AI agent. It is a **scripted vulnerability simulator** (no live LLM inside; responses are deterministic), exposing 14 specialist agents on dedicated ports plus a dashboard on `:9000`. It's the right harness to verify the runner mechanically over the `direct_chat` vector.

```bash
# In a separate terminal, outside this repo:
docker run -d --name dvaa --rm \
  -p 7001-7008:7001-7008 -p 7010-7013:7010-7013 \
  -p 7020-7021:7020-7021 -p 9000:9000 \
  opena2a/dvaa:latest
```

Confirm **LegacyBot** (the most permissive agent, model name `legacybot`, port `7003`) is reachable:

```bash
curl -s http://localhost:7003/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"legacybot","messages":[{"role":"user","content":"ping"}]}' | head -c 200
```

The canonical DVAA target profiles already live in this repo: `targets/dvaa_legacybot.yaml` (LegacyBot, `:7003`) and `targets/dvaa_local.yaml` (HelperBot, `:7002`, with the full agent/port map and per-vector fit notes). You should not need to edit them for the local Docker setup.

> **DVAA fits `direct_chat` (and real-MCP JSON-RPC on `:7010`) only.** Its knowledge base is fixed — there is no external RAG ingest, file-upload, or webhook endpoint, so `rag_corpus` / `document_upload` / `webhook` atomics do **not** run against DVAA. For those vectors use the agent-runner skill or a real target you control (see [docs/targets.md](targets.md)). This quickstart uses `direct_chat`, which DVAA fully supports.

## Step 3 — recon

Back in the atomic-atlas repo:

```bash
atomic-atlas recon --target http://localhost:7003/v1
```

Expected output (abridged):

```
Recon: http://localhost:7003/v1

Entry vectors:
  ✓ direct_chat
  ?  mcp_server  (cannot determine externally)

Guardrails:
  input_filter_detected: False

Suggested ATLAS techniques in scope:
  AML.T0051.000, AML.T0065
```

The recon module probes well-known endpoints (chat completions, OpenAPI / tool schemas, MCP discovery) and suggests applicable ATLAS techniques based on what it finds. LegacyBot has no input filter — a credential-disclosure atomic over `direct_chat` is in scope.

## Step 4 — set up the attacker LLM

PyRIT's `RedTeamingAttack` uses a separate "attacker" LLM to generate and mutate payloads across turns. The same model serves the LLM judge tier. Configure once in repo-root `.env` (auto-loaded; see [docs/install.md](install.md#llm-providers--openai-openrouter-ollama-local-llms) for the full provider matrix):

```dotenv
# .env
OPENAI_API_KEY=sk-...
ATOMIC_ATLAS_LLM_MODEL=gpt-4o            # default; gpt-4o-mini for cheaper
```

For non-OpenAI providers (OpenRouter, Ollama, vLLM, LiteLLM), set `OPENAI_API_BASE` in `.env` too — atomic-atlas detects external providers and trusts the operator's setup. Full setup snippets in [docs/install.md](install.md). (The captured run in [docs/sample_assessment1/sample_execution.md](sample_assessment1/sample_execution.md) used `deepseek/deepseek-v3.2` via OpenRouter — ~30× cheaper than gpt-4o, same evidence quality.)

## Step 5 — run the flagship atomic

```bash
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --authorized
```

What happens under the hood:

1. The runner loads `atomics/AML.T0083/direct_chat.md` (intent + frontmatter).
2. `DirectChatTarget` wraps LegacyBot's chat endpoint; the profile's `target_context` is fed into the attacker LLM's system prompt so its mutations are domain-aware.
3. `RedTeamingAttack` drives a multi-turn attack — the attacker LLM rewrites the credential probe each turn until LegacyBot succumbs or runs out of turns.
4. The two-tier scorer evaluates each run; the atomic's regex `extractors` capture leaked credentials.
5. The result is **appended to the engagement directory** (`./atomic-atlas-engagement/results.jsonl` by default).

Expected output:

```
Running AML.T0083 via direct_chat (5 runs)…

✓ 5/5 success (100%) in 527.6s
Appended to atomic-atlas-engagement/results.jsonl
```

> **Authorization gate.** `--authorized` is required per `exec` invocation. Running atomics against systems you do not own or have written permission to test is unethical and likely illegal.

> **Why so long?** Each run is a full multi-turn adversarial conversation (attacker LLM ↔ target ↔ judge), ×5 runs — most of the wall time is attacker/judge LLM latency, not atomic-atlas or DVAA (DVAA replies instantly). Levers: a faster model, fewer `--runs`, or `ATOMIC_ATLAS_OFFLINE=1` (single-turn, deterministic, no attacker LLM). See [docs/sample_assessment1/sample_execution.md](sample_assessment1/sample_execution.md) for the full timing breakdown.

### Scoring: judge tier with first-class evidence

Each run is scored by an automatic two-tier stack:

1. **LLM judge** — when `OPENAI_API_KEY` is set, PyRIT's `SelfAskTrueFalseScorer` reads the response against the atomic's `## Success criteria`. Produces a verdict + natural-language reasoning.
2. **IndicatorScorer** — any-of-N substring match over `success_indicators`. Auto-fallback when no judge.

Every verdict carries a structured **`evidence`** payload — `tier`, `verdict`, `judge_reasoning`, `matched_indicators`, `extracted` (regex artifacts), `duration_ms`. It rides on each `run_details[i]` in the engagement `results.jsonl`, gets rendered inline by the markdown reporter, and surfaces in the ATLAS Navigator metadata (`evidence_count` / `top_extracted` per technique).

For `AML.T0083` the regex extractors harvest the actual leaked credentials (`sk-dvaa-openai-test-key-…`, `dvaa-admin-secret`, `dvaa-db-password-123`) into `evidence.extracted` — verdict + the artifacts in one pass.

Override the auto-selection per atomic via `scoring: { strategy: indicators }` (skip judge cost when indicators are deterministic ground truth) or globally via `ATOMIC_ATLAS_OFFLINE=1` (disables every LLM call site). Full authoring guide: [`docs/scoring.md`](scoring.md).

## Step 6 — report

Every `exec` and `runbook exec` automatically appends a timestamped entry to `./atomic-atlas-engagement/results.jsonl` (override location with `--engagement DIR` or `ATOMIC_ATLAS_ENGAGEMENT_DIR` in `.env`). Render the engagement-level report:

```bash
# Stakeholder-facing engagement report — one Finding per (atomic × target),
# with verdict (VULNERABLE / PARTIALLY_VULNERABLE / NOT_VULNERABLE / INCONCLUSIVE),
# severity, summary, evidence, and ATLAS mitigations.
atomic-atlas report --format findings --output engagement.md

# Filter to one target or a time window
atomic-atlas report --format findings --target dvaa_legacybot
atomic-atlas report --format findings --since 2026-05-05

# Other formats (also default to the engagement source — no --input needed)
atomic-atlas report --format navigator --output dvaa.layer.json
atomic-atlas report --format coverage
atomic-atlas report --format markdown          # per-run detail view
```

For `AML.T0083` you'll get a **VULNERABLE / HIGH** finding with the extracted credentials inline — see the committed real output in [`docs/sample_assessment1/reports/findings.md`](sample_assessment1/reports/findings.md).

Open [the ATLAS Navigator](https://mitre-atlas.github.io/atlas-navigator/) → "Open Existing Layer" → "Upload from local" → pick `dvaa.layer.json`. You will see your tested techniques color-coded by success rate.

**The engagement directory's structure** (auto-created on first write):

```
atomic-atlas-engagement/
  results.jsonl           # one JSON object per atomic run
  runbook-results.jsonl   # one JSON object per runbook step
  adapted-payloads/       # bundles produced by `adapt --output`
  recon/                  # outputs of `recon` (if you save them here)
  reports/                # rendered findings / navigator / markdown
```

Each JSONL line is stamped with `engagement_id`, `recorded_at`, `target_id`, `atomic_path`, plus the full RunResult. `jq`-friendly. One folder per customer / scope is the natural pattern. See [`docs/cli-reference.md`](cli-reference.md#report) for full filter syntax.

## Step 7a (optional) — generate a target-tuned payload with `adapt`

For atomics where the static seed is generic, `atomic-atlas adapt` generates a target-tuned payload bundle (rationale + payload + suggested observations) using the atomic's intent + the profile's `target_context` + optional prior-run evidence. `atomic-atlas exec --payload-file <bundle>` runs it.

The chained workflow (T0084 harvest → adapt T0083 with `--observed` → exec) is walked end-to-end as **UC2 in [`docs/use-cases.md`](use-cases.md)**. Authoring details + bundle format: [`docs/adapt.md`](adapt.md).

## Step 7b (optional) — chain atomics

Run the next technique in the kill chain — both `direct_chat`, both fit DVAA:

```bash
atomic-atlas exec AML.T0084/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --authorized

atomic-atlas report --format navigator --output dvaa.layer.json
```

The engagement memory accumulates across `exec` runs, so the final Navigator layer reflects every technique you've run against the target — no `--input` needed; `report` reads the engagement directory by default.

> **Tip:** a multi-step chain can be expressed as a runbook and executed in one shot. See [`runbooks/dvaa/`](../runbooks/dvaa/) for 22 DVAA challenges already mapped, and [`docs/agent-runner.md`](agent-runner.md) for the runbook concept.

## Step 8 (optional) — interactive review with `--hitl`

For engagement work against production-like targets — or just for debugging payload generation — pass `--hitl` to gate every outbound message on operator confirmation:

```bash
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --authorized --hitl
```

Each send pauses with the about-to-go-out payload; you respond:

- `y` — forward to the target
- `s` — show the full message body (it's truncated by default)
- `n` — skip this turn (counted as a failure for scoring)
- `a` — abort the run / chain entirely

Works on both `atomic-atlas exec` and `atomic-atlas runbook exec`. For runbooks, abort propagates through the chain — remaining steps are marked skipped.

For domain-aware payload mutation, set the `target_context` block in your target profile — see [docs/targets.md](targets.md#target_context--domain-aware-payload-adaptation).

## Where to go next

- **The same run, captured verbatim** — [`docs/sample_assessment1/sample_execution.md`](sample_assessment1/sample_execution.md): every command + real output + how to read the finding.
- **Three end-to-end walkthroughs** — [`docs/use-cases.md`](use-cases.md): smoke a single technique, run a chained kill chain with `adapt`, run a full engagement runbook.
- **CLI flag reference** — every subcommand and flag with copy-pasteable examples: [`docs/cli-reference.md`](cli-reference.md).
- **Scoring + Evidence** — when to use `judge_guidance` / `judge_examples` / `extractors`, the Evidence schema: [`docs/scoring.md`](scoring.md).
- **Payload adapter** — bundle format, prompt structure, observed-evidence selection rules: [`docs/adapt.md`](adapt.md).
- **Authoring atomics** — copy `atomics/_TEMPLATE/vector_template.md`, fill in frontmatter + body sections, run `atomic-atlas validate`, then `python scripts/generate_index.py`. See [SPEC.md](../SPEC.md).
- **Testing a non-DVAA target** — see [docs/targets.md](targets.md) for profile authoring and the auth-scheme reference.
- **Hard-coded adapter doesn't fit your target** — use the [agent runner](agent-runner.md). The Claude Code skill (`/atomic-atlas`) and the MCP server (`atomic-atlas-mcp`) reason about novel targets and adapt delivery on the fly.
- **PyRIT — the dependency explained** — [docs/pyrit.md](pyrit.md); install/troubleshooting in [docs/install.md](install.md).
