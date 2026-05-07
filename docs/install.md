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

PyRIT is the orchestration backbone for `exec`. It generates and mutates payloads (via `RedTeamingOrchestrator`), drives multi-turn attacks, and scores responses. atomic-atlas extends PyRIT with `PromptTarget` subclasses for the agentic vectors PyRIT does not cover natively (RAG injection, MCP tool poisoning, tool response interception, document upload, webhook).

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

The judge tier and the attacker LLM both use the same OpenAI-compatible client. Point them anywhere via two env vars:

| Provider | `OPENAI_API_BASE` | `OPENAI_API_KEY` | Example `--model` |
|---|---|---|---|
| **OpenAI** (default) | `https://api.openai.com/v1` | real `sk-...` | `gpt-4o`, `gpt-4o-mini` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `sk-or-v1-...` | `google/gemma-2-9b-it:free`, `qwen/qwen-2.5-7b-instruct:free`, `mistralai/mistral-7b-instruct:free`, `meta-llama/llama-3.2-3b-instruct:free` |
| **Ollama** (local) | `http://localhost:11434/v1` | any (Ollama ignores it) | `qwen2.5:7b`, `gemma2:9b`, `llama3.2:3b` |
| **vLLM** (local/server) | `http://your-host:8000/v1` | any | the model name vLLM was launched with |
| **LiteLLM proxy** | `http://your-proxy:4000/v1` | proxy's key | anything LiteLLM is configured to route |

Atomic-atlas detects "external provider" automatically: when `OPENAI_API_BASE` points anywhere other than `api.openai.com`, the placeholder-key check is skipped and the operator's setup is trusted (the upstream rejects invalid auth at request time).

**OpenRouter (cheap or free models) — full setup:**

```bash
export OPENAI_API_BASE=https://openrouter.ai/api/v1
export OPENAI_API_KEY=sk-or-v1-your-key-here

atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized \
  --model "google/gemma-2-9b-it:free"
```

`--model` is per-run; you can also set `ATOMIC_ATLAS_LLM_MODEL=...` once for the shell. The model is used for both the attacker LLM (in `RedTeamingAttack`) and the judge tier scorer.

**Ollama (local) — full setup:**

```bash
# Bring up Ollama with a model:
ollama serve
ollama pull qwen2.5:7b

# Point atomic-atlas at it:
export OPENAI_API_BASE=http://localhost:11434/v1
unset OPENAI_API_KEY     # not required by Ollama

atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized \
  --model qwen2.5:7b
```

**Per-call overrides** (different judge model than attacker model):

```bash
# Use cheap model for the attacker LLM, but the atomic's frontmatter can
# pin a stronger judge model for evaluation:
#
#   scoring:
#     judge_model: gpt-4o
#
# Attacker uses --model / ATOMIC_ATLAS_LLM_MODEL; judge uses scoring.judge_model.
```

**Cost lever cheat-sheet** (high-cost → low-cost):

| Setup | Per-atomic cost (5 runs) | Notes |
|---|---|---|
| `gpt-4o` (default) | ~$0.30-0.80 | Honest verdicts, fast |
| `--model gpt-4o-mini` | ~$0.02-0.05 | Slight judge-quality hit; usually fine |
| OpenRouter `:free` model | $0 | Rate-limited; some 429s |
| Ollama local | $0 | Bound by your hardware |
| `ATOMIC_ATLAS_OFFLINE=1` | $0 | No LLM at all; falls back to deterministic indicator scoring |

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

`exec` with `RedTeamingOrchestrator`-class atomics needs an attacker LLM to generate payload variants. atomic-atlas defaults to OpenAI, configurable via env:

```bash
export OPENAI_API_KEY=sk-...
export ATOMIC_ATLAS_ATTACKER_MODEL=gpt-4o            # default
export OPENAI_API_BASE=https://api.openai.com/v1     # default
```

To use a non-OpenAI provider (Anthropic, Bedrock, Ollama, etc.), point `OPENAI_API_BASE` at an OpenAI-compatible proxy like [LiteLLM](https://github.com/BerriAI/litellm). PyRIT 0.13 does not yet ship a first-class Anthropic chat target.
