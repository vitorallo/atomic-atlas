# Quick start

Goal of this doc: take you from a clean machine to a successful `recon → exec → report` cycle against a vulnerable AI agent in about ten minutes.

## What you'll have at the end

- atomic-atlas installed locally
- A vulnerable AI agent ([DVAA](https://github.com/opena2a-org/damn-vulnerable-ai-agent)) running on `localhost:8080`
- A successful run of the flagship atomic `AML.T0051.001/rag_corpus` (Indirect Prompt Injection via RAG)
- An ATLAS Navigator layer JSON you can paste into [the Navigator](https://mitre-atlas.github.io/atlas-navigator/)

## Prerequisites

- **Python 3.10–3.13** (PyRIT 0.13 does not yet support 3.14). Check with `python3 --version`.
- **Docker** for running DVAA locally.
- An **OpenAI API key** (or an OpenAI-compatible proxy) for the attacker LLM that PyRIT's `RedTeamingAttack` uses. Set `OPENAI_API_KEY=...` in your environment.

If anything fails during install, see [docs/install.md](install.md) for the install matrix and common-error troubleshooting.

## Step 1 — install atomic-atlas

```bash
git clone https://github.com/<your-fork>/atomic-atlas.git
cd atomic-atlas
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[orchestrator]'    # base + PyRIT for `exec`
```

> **Why an extra?** PyRIT is heavy (~1 GB transitive) and only required for `atomic-atlas exec`. The base install is enough for `list / recon / report / validate` and for running the MCP server. See [docs/install.md](install.md).

Sanity-check the install:

```bash
atomic-atlas --help
atomic-atlas list                    # should print 12 atomics
atomic-atlas validate                # should end with "All N atomic(s) valid."
```

## Step 2 — bring up DVAA

DVAA is an intentionally vulnerable AI agent that exposes RAG, tools, file upload, and a chat surface — exactly the stack atomic-atlas is built to test.

```bash
# In a separate terminal, outside this repo:
git clone https://github.com/opena2a-org/damn-vulnerable-ai-agent.git
cd damn-vulnerable-ai-agent
# Follow the upstream README — typically:
docker compose up -d
```

Confirm it's reachable:

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"default","messages":[{"role":"user","content":"ping"}]}' | head -c 200

curl -s http://localhost:8000/api/v1/heartbeat       # ChromaDB heartbeat
```

If your DVAA setup needs an API key, export it now:

```bash
export DVAA_API_KEY=...
```

A canonical DVAA target profile already lives in this repo at `targets/dvaa_local.yaml`. You should not need to edit it for the local Docker setup.

> If you don't want to set up DVAA right now, see [docs/targets.md](targets.md) for the Lakera Gandalf alternative — much faster, but limited to `direct_chat`, so it doesn't exercise atomic-atlas's agentic vectors.

## Step 3 — recon

Back in the atomic-atlas repo:

```bash
atomic-atlas recon --target http://localhost:8080
```

Expected output (abridged):

```
Recon: http://localhost:8080

Entry vectors:
  ✓ direct_chat
  ✓ rag_corpus
  ✓ tool_response
  ?  mcp_server  (cannot determine externally)

Tools exposed:
  - send_email
  - fetch_url
  ...

Suggested ATLAS techniques in scope:
  AML.T0051.001, AML.T0053, AML.T0086, ...
```

The recon module probes well-known endpoints (chat completions, OpenAPI / tool schemas, MCP discovery, webhook paths) and suggests applicable ATLAS techniques based on what it finds.

## Step 4 — set up the attacker LLM

PyRIT's `RedTeamingAttack` uses a separate "attacker" LLM to generate and mutate injected payloads. The same model serves the LLM judge tier. Configure once in repo-root `.env` (auto-loaded; see [docs/install.md](install.md#llm-providers--openai-openrouter-ollama-local-llms) for the full provider matrix):

```dotenv
# .env
OPENAI_API_KEY=sk-...
ATOMIC_ATLAS_LLM_MODEL=gpt-4o            # default; gpt-4o-mini for cheaper
```

For non-OpenAI providers (OpenRouter, Ollama, vLLM, LiteLLM), set `OPENAI_API_BASE` in `.env` too — atomic-atlas detects external providers and trusts the operator's setup. Full setup snippets in [docs/install.md](install.md).

## Step 5 — run the flagship atomic

```bash
atomic-atlas exec AML.T0051.001/rag_corpus \
  --target http://localhost:8080 \
  --profile targets/dvaa_local.yaml \
  --authorized
```

What happens under the hood:

1. The runner loads `atomics/AML.T0051.001/rag_corpus.md` (intent + frontmatter).
2. `RAGCorpusTarget.setup()` injects the poisoned document into DVAA's ChromaDB.
3. The `RedTeamingAttack` drives a multi-turn attack against DVAA's chat endpoint, with the attacker LLM mutating the trigger as needed.
4. PyRIT's scorer evaluates each run.
5. `RAGCorpusTarget.cleanup()` removes the injected document.
6. Results are written to `results.json` (appended if the file exists).

Expected output:

```
Running AML.T0051.001 via rag_corpus (5 runs)…

✓ 4/5 success (80%) in 12.7s
Results written to results.json
```

> **Authorization gate.** `--authorized` is required per `exec` invocation. Running atomics against systems you do not own or have written permission to test is unethical and likely illegal.

### Scoring: judge tier with first-class evidence

Each run is scored by an automatic two-tier stack:

1. **LLM judge** — when `OPENAI_API_KEY` is set, PyRIT's `SelfAskTrueFalseScorer` reads the response against the atomic's `## Success criteria`. Produces a verdict + natural-language reasoning.
2. **IndicatorScorer** — any-of-N substring match over `success_indicators`. Auto-fallback when no judge.

Every verdict carries a structured **`evidence`** payload — `tier`, `verdict`, `judge_reasoning`, `matched_indicators`, `extracted` (regex artifacts), `duration_ms`. It rides on each `run_details[i]` in `results.json`, gets rendered inline by the markdown reporter, and surfaces in the ATLAS Navigator metadata (`evidence_count` / `top_extracted` per technique).

For credential / config-disclosure atomics, optional `extractors:` frontmatter captures actual content into `evidence.extracted`:

```bash
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized
```

Against LegacyBot the regex extractors harvest the actual leaked credentials (`sk-dvaa-openai-test-key-…`, `dvaa-admin-secret`) into `evidence.extracted` — verdict + the artifacts in one pass.

Override the auto-selection per atomic via `scoring: { strategy: indicators }` (skip judge cost when indicators are deterministic ground truth) or globally via `ATOMIC_ATLAS_OFFLINE=1` (disables every LLM call site). Full authoring guide: [`docs/scoring.md`](scoring.md).

## Step 6 — report

Every `exec` and `runbook exec` automatically appends a timestamped entry to `./atomic-atlas-engagement/results.jsonl` (override location with `--engagement DIR` or `ATOMIC_ATLAS_ENGAGEMENT_DIR` in `.env`). After running a few atomics, render the engagement-level report:

```bash
# Stakeholder-facing engagement report — one Finding per (atomic × target),
# with verdict (VULNERABLE / PARTIALLY_VULNERABLE / NOT_VULNERABLE / INCONCLUSIVE),
# severity, summary, evidence, and ATLAS mitigations.
atomic-atlas report --format findings --output engagement.md

# Filter to one target or a time window
atomic-atlas report --format findings --target dvaa_legacybot
atomic-atlas report --format findings --since 2026-05-05

# Other formats (also default to engagement source — no --input needed)
atomic-atlas report --format navigator --output dvaa.layer.json
atomic-atlas report --format coverage
atomic-atlas report --format markdown          # per-run detail view
```

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

Run the next technique in the kill chain:

```bash
atomic-atlas exec AML.T0053/tool_response \
  --target http://localhost:8080 \
  --profile targets/dvaa_local.yaml \
  --authorized

atomic-atlas exec AML.T0086/mcp_server \
  --target http://localhost:8080 \
  --profile targets/dvaa_local.yaml \
  --authorized

atomic-atlas report --input results.json --format navigator --output dvaa.layer.json
```

`results.json` accumulates across `exec` runs, so the final Navigator layer reflects the full chain `T0051.001 → T0053 → T0086`.

> **Tip:** the same chain can be expressed as a runbook and executed in one shot. See [`runbooks/dvaa/`](../runbooks/dvaa/) for 22 DVAA challenges already mapped, and [`docs/agent-runner.md`](agent-runner.md) for the runbook concept.

## Step 8 (optional) — interactive review with `--hitl`

For engagement work against production-like targets — or just for debugging payload generation — pass `--hitl` to gate every outbound message on operator confirmation:

```bash
atomic-atlas exec AML.T0051.001/rag_corpus \
  --target http://localhost:8080 \
  --profile targets/dvaa_local.yaml \
  --authorized --hitl
```

Each send pauses with the about-to-go-out payload; you respond:

- `y` — forward to the target
- `s` — show the full message body (it's truncated by default)
- `n` — skip this turn (counted as a failure for scoring)
- `a` — abort the run / chain entirely

Works on both `atomic-atlas exec` and `atomic-atlas runbook exec`. For runbooks, abort propagates through the chain — remaining steps are marked skipped.

For domain-aware payload mutation (when `RedTeamingAttack`-tagged atomics are running), set the `target_context` block in your target profile — see [docs/targets.md](targets.md#target_context--domain-aware-payload-adaptation).

## Where to go next

- **Three end-to-end walkthroughs** — [`docs/use-cases.md`](use-cases.md): smoke a single technique, run a chained kill chain with `adapt`, run a full engagement runbook.
- **CLI flag reference** — every subcommand and flag with copy-pasteable examples: [`docs/cli-reference.md`](cli-reference.md).
- **Scoring + Evidence** — when to use `judge_guidance` / `judge_examples` / `extractors`, the Evidence schema: [`docs/scoring.md`](scoring.md).
- **Payload adapter** — bundle format, prompt structure, observed-evidence selection rules: [`docs/adapt.md`](adapt.md).
- **Authoring atomics** — copy `atomics/_TEMPLATE/vector_template.md`, fill in frontmatter + body sections, run `atomic-atlas validate`. See [SPEC.md](../SPEC.md).
- **Testing a non-DVAA target** — see [docs/targets.md](targets.md) for profile authoring and the auth-scheme reference.
- **Hard-coded adapter doesn't fit your target** — use the [agent runner](agent-runner.md). The Claude Code skill (`/atomic-atlas`) and the MCP server (`atomic-atlas-mcp`) reason about novel targets and adapt delivery on the fly.
- **PyRIT troubleshooting** — see [docs/install.md](install.md).
