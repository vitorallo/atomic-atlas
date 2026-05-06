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
- An **OpenAI API key** (or an OpenAI-compatible proxy) for the attacker LLM that PyRIT's `RedTeamingOrchestrator` uses. Set `OPENAI_API_KEY=...` in your environment.

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

PyRIT's `RedTeamingOrchestrator` uses a separate "attacker" LLM to generate and mutate injected payloads. Configure it via env:

```bash
export OPENAI_API_KEY=sk-...
export ATOMIC_ATLAS_ATTACKER_MODEL=gpt-4o            # default
```

To use a non-OpenAI provider (Anthropic, Bedrock, Ollama, …), point `OPENAI_API_BASE` at a [LiteLLM](https://github.com/BerriAI/litellm) proxy. PyRIT 0.13 does not ship a first-class Anthropic chat target.

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
3. The `RedTeamingOrchestrator` drives a multi-turn attack against DVAA's chat endpoint, with the attacker LLM mutating the trigger as needed.
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

## Step 6 — report

```bash
# Coverage matrix (terminal)
atomic-atlas report --input results.json --format coverage

# Markdown report (terminal or file)
atomic-atlas report --input results.json --format markdown

# ATLAS Navigator layer JSON
atomic-atlas report --input results.json --format navigator --output dvaa.layer.json
```

Open [the ATLAS Navigator](https://mitre-atlas.github.io/atlas-navigator/) → "Open Existing Layer" → "Upload from local" → pick `dvaa.layer.json`. You will see your tested techniques color-coded by success rate.

## Step 7 (optional) — chain atomics

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

## Where to go next

- **Authoring atomics** — copy `atomics/_TEMPLATE/vector_template.md`, fill in frontmatter + body sections, run `atomic-atlas validate`. See [SPEC.md](../SPEC.md).
- **Testing a non-DVAA target** — see [docs/targets.md](targets.md) for profile authoring and the auth-scheme reference.
- **Hard-coded adapter doesn't fit your target** — use the [agent runner](agent-runner.md). The Claude Code skill (`/atomic-atlas`) and the MCP server (`atomic-atlas-mcp`) reason about novel targets and adapt delivery on the fly.
- **PyRIT troubleshooting** — see [docs/install.md](install.md).
