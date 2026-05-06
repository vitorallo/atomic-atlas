# Targets

A **target** is an AI agent under test. atomic-atlas reaches it through one or more entry vectors. Two pieces of information are needed for any test:

1. The **target URL** — passed to `--target`.
2. A **target profile** — a YAML file passed to `--profile` that tells the runner how to talk to the target's RAG, MCP, file API, webhook, etc.

This page explains the profile format and walks through two recommended starter targets:

- **DVAA (Damn Vulnerable AI Agent)** — local, exposes the full agentic surface (RAG, tools, file upload). The canonical demo target for atomic-atlas.
- **Lakera Gandalf** — hosted, free, no setup. Excellent for getting familiar with prompt injection mechanics, but limited to `direct_chat` so it does not exercise atomic-atlas's unique value (the agentic vectors).

## Target profile format

Profiles live in `targets/*.yaml`. They have one top-level field (`base_url`) and an `adapters` map keyed by interaction vector. Auth is always referenced via env vars — credentials are never written into the file.

```yaml
base_url: http://localhost:8080

adapters:
  rag_corpus:
    type: chroma                 # or azure_search | http_ingest
    host: localhost:8000
    collection: knowledge

  mcp_server:
    type: http_registry_stub
    registry_url: http://localhost:8080/mcp/tools
    auth:
      type: bearer
      token: ${MCP_TOKEN}

  tool_response:
    type: mock_server
    port: 9090

  document_upload:
    type: openai_compatible
    upload_url: http://localhost:8080/v1/files
    api_key: ${TARGET_API_KEY}

  webhook:
    webhook_url: http://localhost:8080/inbound
    callback_port: 0             # 0 = kernel-assigned free port
```

### Auth schemes

| Scheme | Adapter config |
|---|---|
| Bearer token | `auth: {type: bearer, token: ${TOKEN_VAR}}` |
| API key in header | `auth: {type: api_key, header: X-API-Key, key: ${KEY_VAR}}` |
| Bare `api_key` field (becomes `Authorization: Bearer ...`) | `api_key: ${KEY_VAR}` |
| HMAC (webhooks) | `auth: {hmac_secret: ${HMAC_VAR}}` |
| Azure DefaultAzureCredential | (planned — v0.2) |

Everything inside `${...}` is resolved from process env at runtime. If the env var is missing, the literal `${VAR}` string is left in place and the request will fail at HTTP time — by design, so you see exactly which credential is missing.

## DVAA — the canonical demo target

[Damn Vulnerable AI Agent](https://github.com/opena2a-org/damn-vulnerable-ai-agent) (DVAA) is an intentionally vulnerable agent that exposes RAG, tool use, and file upload surfaces. atomic-atlas ships a profile for the local Docker setup at `targets/dvaa_local.yaml`:

```yaml
# targets/dvaa_local.yaml (in this repo)
base_url: http://localhost:8080

adapters:
  direct_chat:
    type: openai_compatible
    api_key: ${DVAA_API_KEY}
    model: default

  rag_corpus:
    type: chroma
    host: localhost:8000
    collection: default

  tool_response:
    type: mock_server
    port: 9090

  document_upload:
    type: openai_compatible
    upload_url: http://localhost:8080/v1/files
    delete_url: http://localhost:8080/v1/files/{file_id}
    model: default
    api_key: ${DVAA_API_KEY}

  webhook:
    webhook_url: http://localhost:8080/inbound
    callback_port: 0

  mcp_server:
    type: http_registry_stub
    registry_url: http://localhost:8080/mcp/tools
```

### Bring DVAA up locally

> Follow the upstream DVAA project's README for the authoritative steps. The summary below is a sketch — exact ports, env vars, and compose flags are owned by that repo.

```bash
# 1. Clone and start DVAA per its README.
git clone https://github.com/opena2a-org/damn-vulnerable-ai-agent.git
cd damn-vulnerable-ai-agent
# (follow upstream setup — typically docker compose up)

# 2. Confirm DVAA is reachable.
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"default","messages":[{"role":"user","content":"hi"}]}'

# 3. Confirm DVAA's ChromaDB is reachable.
curl http://localhost:8000/api/v1/heartbeat

# 4. Set any env vars referenced in the profile.
export DVAA_API_KEY=...   # if DVAA requires one
```

### Run an atomic against DVAA

```bash
# Lightweight: see what DVAA exposes.
atomic-atlas recon --target http://localhost:8080

# Full: run the flagship indirect-prompt-injection-via-RAG atomic.
atomic-atlas exec AML.T0051.001/rag_corpus \
  --target http://localhost:8080 \
  --profile targets/dvaa_local.yaml \
  --authorized

# Build the ATLAS Navigator layer.
atomic-atlas report --input results.json --format navigator --output dvaa.layer.json
```

The Navigator layer is paste-ready into [https://mitre-atlas.github.io/atlas-navigator/](https://mitre-atlas.github.io/atlas-navigator/).

## Lakera Gandalf — alternative, low-friction target

[Lakera Gandalf](https://gandalf.lakera.ai/) is a free, hosted prompt-injection challenge. It only exposes `direct_chat`, so it is **not** a target for the atomic-atlas CLI's agentic vectors — but it is an excellent way to get familiar with PyRIT and prompt injection mechanics before you set up DVAA.

PyRIT ships a built-in `GandalfTarget`. To run one of atomic-atlas's `direct_chat` atomics against it, use the **agent runner** (Claude Code skill) — `direct_chat` is a documented fallback case where the skill bypasses the CLI:

```
/atomic-atlas exec AML.T0051.000/direct_chat --target https://gandalf.lakera.ai/
```

Or use PyRIT directly outside atomic-atlas if you just want to play:

```python
from pyrit.prompt_target import GandalfTarget, GandalfLevel
target = GandalfTarget(level=GandalfLevel.LEVEL_1)
# ... PyRIT orchestrator drives it ...
```

Why Gandalf is **not** the canonical demo: atomic-atlas exists to test agentic vectors that PyRIT, garak, and Promptfoo don't reach. Gandalf is a single-turn, chat-only challenge — exactly the gap that already-existing tools cover well. Use it for prompt-injection familiarity, then move to DVAA for the real atomic-atlas story.

## Writing your own target profile

```bash
cp targets/dvaa_local.yaml targets/my_target.yaml
$EDITOR targets/my_target.yaml             # adjust base_url + adapters
atomic-atlas recon --target https://my-agent.example.com
# → use recon output to figure out which adapters to wire up
atomic-atlas exec AML.T0051.001/rag_corpus \
  --target https://my-agent.example.com \
  --profile targets/my_target.yaml \
  --authorized
```

Authorization is mandatory. Do not run atomics against systems you do not own or have written permission to test.

## Adapter coverage

The CLI ships adapters for five vectors. The other seven vectors (`direct_chat`, `system_prompt`, `web_fetch`, `email`, `a2a_message`, `computer_use`, `model_api`) are reachable only via the [agent runner](agent-runner.md) — the Claude Code skill or the MCP server. If you try to `exec` an atomic for one of those vectors, the CLI raises `UnsupportedVectorError` with a hint pointing you at the agent runner.

| Vector | CLI adapter | Notes |
|---|---|---|
| `rag_corpus` | ✓ | ChromaDB / Azure AI Search / HTTP ingest |
| `mcp_server` | ✓ (stub) | `http_registry_stub` — placeholder; real MCP target is v0.2 |
| `tool_response` | ✓ | mock HTTP server returning poisoned response |
| `document_upload` | ✓ | OpenAI-compatible file API |
| `webhook` | ✓ | POST + callback listener (port 0 by default) |
| `direct_chat` | (skill / MCP) | Use the agent runner |
| `system_prompt` | (skill / MCP) | Use the agent runner |
| `web_fetch` | (skill / MCP) | Use the agent runner |
| `email` | (skill / MCP) | Use the agent runner |
| `a2a_message` | (skill / MCP) | Use the agent runner |
| `computer_use` | (skill / MCP) | Use the agent runner |
| `model_api` | (skill / MCP) | Use the agent runner |
