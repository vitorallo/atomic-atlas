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
