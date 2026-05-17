# Install

atomic-atlas has a **layered install model**. The base install is small and lets you author atomics, validate the catalog, fingerprint targets, and run the MCP server. Adding the `[orchestrator]` extra pulls in PyRIT and unlocks `atomic-atlas exec` — actually running atomics against a target.

## Install matrix

| Command | Adds | Pulls in PyRIT? | Lets you run |
|---|---|---|---|
| `pip install atomic-atlas` | Parser, schema, recon, reporters, CLI | No | `list`, `recon`, `report`, `validate` |
| `pip install 'atomic-atlas[mcp-server]'` | Above + MCP SDK | No | `atomic-atlas-mcp` (read-only MCP server) |
| `pip install 'atomic-atlas[orchestrator]'` | Above + PyRIT and its transitive deps | **Yes** | `exec` — actually executes atomics |
| `pip install 'atomic-atlas[orchestrator,mcp-server,dev]'` | Above + pytest | Yes | Everything, including the test suite |

## Why PyRIT is optional

PyRIT is the orchestration backbone for `exec`. It generates and mutates payloads (via `RedTeamingAttack`), drives multi-turn attacks, and scores responses. atomic-atlas extends PyRIT with `PromptTarget` subclasses for the agentic vectors PyRIT does not cover natively (RAG injection, MCP tool poisoning, tool response interception, document upload, webhook).

But PyRIT is **heavy**. Its transitive dependencies include `azure-ai-*`, `openai`, `anthropic`, `chromadb`, `accelerate`, `transformers`, and more — easily 1+ GB of installs. If you only want to:

- write a new atomic and `validate` it
- recon a target to see which vectors it exposes
- run the MCP server so an external agent (Claude, Hermes, GPT, Gemini) can drive a session
- generate a report from someone else's `results.json`

…you do not need PyRIT. The base install handles all of that and is dramatically faster to install in CI or on a contributor's laptop.

When you actually want to execute an atomic — the keynote-demo path — you install with the `[orchestrator]` extra. The CLI checks for PyRIT up front and prints a clear install hint if you forgot.

## Python version

PyRIT 0.13 supports **Python 3.10 through 3.13**. atomic-atlas itself works on 3.10+, but if you intend to install `[orchestrator]`, you must use a 3.10–3.13 interpreter. Python 3.14 is **not** yet supported by PyRIT.

```bash
python3 --version    # confirm 3.10, 3.11, 3.12, or 3.13
python3.12 -m venv .venv
source .venv/bin/activate
pip install 'atomic-atlas[orchestrator]'
```

## From source (development)

```bash
git clone https://github.com/<your-fork>/atomic-atlas.git
cd atomic-atlas
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[orchestrator,mcp-server,dev]'
pytest -q                                 # smoke-test
atomic-atlas validate                     # check the seed catalog
```

## Verifying the install

| Check | Command | Expected |
|---|---|---|
| CLI is on PATH | `atomic-atlas --help` | usage banner |
| Catalog is valid | `atomic-atlas validate` | `All N atomic(s) valid.` |
| Lightweight commands work | `atomic-atlas list` | table of seed atomics |
| PyRIT is installed | `python3 -c "import pyrit; print(pyrit.__version__)"` | a version number ≥ 0.5 |
| MCP server starts | `atomic-atlas-mcp` (Ctrl-C to stop) | starts on stdio without error |

## LLM providers — OpenAI, OpenRouter, Ollama, local LLMs

The judge tier and the attacker LLM both use the same OpenAI-compatible client. Point them anywhere via three env vars in your repo-root `.env` (auto-loaded on import; `.env` wins over the shell):

| Provider | `OPENAI_API_BASE` | `OPENAI_API_KEY` | `ATOMIC_ATLAS_LLM_MODEL` |
|---|---|---|---|
| **OpenAI** (default) | `https://api.openai.com/v1` | real `sk-...` | `gpt-4o`, `gpt-4o-mini` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `sk-or-v1-...` | `google/gemma-2-9b-it:free`, `qwen/qwen-2.5-7b-instruct:free`, `mistralai/mistral-7b-instruct:free`, `meta-llama/llama-3.2-3b-instruct:free` |
| **Ollama** (local) | `http://localhost:11434/v1` | (omit — Ollama ignores it) | `qwen2.5:7b`, `gemma2:9b`, `llama3.2:3b` |
| **vLLM** (local/server) | `http://your-host:8000/v1` | (any) | the model name vLLM was launched with |
| **LiteLLM proxy** | `http://your-proxy:4000/v1` | proxy's key | anything LiteLLM is configured to route |

Atomic-atlas detects "external provider" automatically: when `OPENAI_API_BASE` points anywhere other than `api.openai.com`, the placeholder-key check is skipped and the operator's setup is trusted (the upstream rejects invalid auth at request time).

**OpenRouter (free or super-cheap models)** — drop into `.env`:

```dotenv
# .env
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-v1-your-key-here
ATOMIC_ATLAS_LLM_MODEL=google/gemma-2-9b-it:free
```

Then run normally:

```bash
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized
```

The same model is used by the attacker LLM (in `RedTeamingAttack`) and the judge tier scorer. Per-atomic judge override is available in the atomic's frontmatter if you want a stronger judge than attacker:

```yaml
# atomics/<technique>/<vector>.md
scoring:
  judge_model: gpt-4o   # judge uses this; attacker uses ATOMIC_ATLAS_LLM_MODEL
```

**Ollama (local)** — drop into `.env`:

```dotenv
# .env
OPENAI_API_BASE=http://localhost:11434/v1
ATOMIC_ATLAS_LLM_MODEL=qwen2.5:7b
# OPENAI_API_KEY left unset; Ollama doesn't validate it
```

Bring up Ollama with the model first:

```bash
ollama serve &
ollama pull qwen2.5:7b
```

Then run as usual. No CLI flag changes needed — the `.env` is the single source of truth.

**Cost lever cheat-sheet** (high-cost → low-cost; pick one in `.env`):

| Setup | Per-atomic cost (5 runs) | Notes |
|---|---|---|
| `gpt-4o` (OpenAI) | ~$0.30-0.80 | Strongest honest verdicts; default if you don't pin anything else |
| `gpt-4o-mini` (OpenAI) | ~$0.02-0.05 | Slight judge-quality hit; usually fine |
| **`deepseek/deepseek-v3.2` (OpenRouter)** | **~$0.01-0.03** | **Recommended cheap default.** Strong on strict-JSON judge prompts and multi-turn `RedTeamingAttack`. Verified end-to-end against DVAA (2/2 success in 150s). |
| `deepseek/deepseek-v4-flash` (OpenRouter) | ~$0.01-0.03 | Slightly cheaper than v3.2, but OpenRouter sometimes routes it through the `AtlasCloud` backend which Cloudflare-blocks PyRIT's adversarial prompts (HTTP 403). v3.2 routes more reliably; prefer it. |
| `google/gemma-3-12b-it` (OpenRouter) | ~$0.005-0.02 | Even cheaper; older model, judge quality acceptable for smoke testing |
| OpenRouter `:free` model | $0 | Rate-limited (429s) and provider-side slowness; multi-turn paths can stall — use for single-turn smoke only |
| Ollama local | $0 | Bound by your hardware |
| `ATOMIC_ATLAS_OFFLINE=1` (in `.env`) | $0 | No LLM at all; falls back to deterministic indicator scoring |

> **Caveat: Gemma 4 26b paid (`google/gemma-4-26b-a4b-it`) handles single-turn judge calls fine but stalls in PyRIT's multi-turn `RedTeamingAttack` — long adversarial prompts hit per-turn latency that compounds across runs. Skip it for multi-turn atomics; DeepSeek v4 flash is the cheap-and-reliable default for our workload.

## Common errors

### `PyRITNotInstalledError: PyRIT is required for atomic execution but is not installed.`

You ran `atomic-atlas exec ...` (or imported a target and instantiated it) on a base install. Resolution:

```bash
pip install 'atomic-atlas[orchestrator]'
```

### `ERROR: Could not find a version that satisfies the requirement pyrit`

You are on Python 3.14, which PyRIT does not yet support. Recreate your venv with 3.12:

```bash
deactivate
rm -rf .venv
python3.12 -m venv .venv && source .venv/bin/activate
pip install 'atomic-atlas[orchestrator]'
```

### `ERROR: vector 'rag_corpus' requires adapter configuration in --profile.`

Pass `--profile <yaml>` to `exec`, or write a profile inline. The CLI prints the expected adapter stanza when it errors. See [docs/targets.md](targets.md).

### `UnsupportedVectorError: Vector 'direct_chat' has no deterministic CLI adapter.`

The CLI ships adapters for five vectors: `rag_corpus`, `mcp_server`, `tool_response`, `document_upload`, `webhook`. The other seven vectors (`direct_chat`, `system_prompt`, `web_fetch`, `email`, `a2a_message`, `computer_use`, `model_api`) are reachable only via the agent runner — Claude Code skill or the MCP server. The error message gives you the invocation hint.

### `ValueError: Central memory instance has not been set.`

You called a runner function from your own Python code without going through `runner.run_atomic`. Fix:

```python
from atomic_atlas.runner import _ensure_pyrit_initialized
_ensure_pyrit_initialized()
# ...then instantiate targets, build orchestrators, etc.
```

By default this initializes an in-memory SQLite store. Override with `ATOMIC_ATLAS_PYRIT_DB=/path/to/persistent.db` if you want durable memory.

## Attacker LLM

`exec` with multi-turn atomics (frontmatter `multi_turn: true`, default) uses an attacker LLM to generate payload variants. The same model serves the LLM judge tier. Configure in repo-root `.env` — see the **LLM providers** section above for OpenRouter / Ollama / vLLM / LiteLLM-specific snippets.
