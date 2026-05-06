# Agent runner

The agent runner is a layer **above** the CLI. The CLI is the deterministic primitive layer; the agent runner reasons about which atomic to run, adapts payloads to the observed target, evaluates success semantically, and chains atomics into a kill chain. The agent only bypasses the CLI when no adapter exists for the vector or for the target's specific backend.

Two implementations, one contract:

- **Claude Code skill** — for users in a Claude Code session.
- **MCP server** — for any MCP-capable agent (Hermes, GPT-4o, Gemini, AutoGen, LangChain, …).

Both wrap the same atomic-atlas CLI. They do not re-implement parsing, target instantiation, orchestration, scoring, or result emission.

## When to use the agent runner instead of the CLI

| Situation | Use |
|---|---|
| The vector has a CLI adapter and your target matches it | **CLI** — straight `atomic-atlas exec` |
| The vector is `direct_chat`, `system_prompt`, `web_fetch`, `email`, `a2a_message`, `computer_use`, or `model_api` | **Agent runner** (CLI raises `UnsupportedVectorError` and points you here) |
| The vector has a CLI adapter but your target uses a backend the adapter doesn't know (e.g., Weaviate when adapters are ChromaDB / Azure AI Search / HTTP ingest) | **Agent runner** |
| Deterministic substring scoring is too weak — success requires semantic judgment | **Agent runner** |
| You want to adapt payload variants to observed target context (tool names, model family, system prompt fragments) | **Agent runner** |

## Claude Code skill

Defined in [`skill/atomic-atlas.md`](../skill/atomic-atlas.md). Loaded automatically by Claude Code when the repo is on disk.

```
/atomic-atlas exec AML.T0051.001/rag_corpus --target http://custom-agent.local
```

The skill's flow: list atomics → recon target → reason about delivery → construct profile → call `atomic-atlas exec` → read results → fall back to manual delivery only when one of the four trigger conditions above fires → report.

## MCP server

Read-only stub in v0.1. Exposes three tools, all PyRIT-free:

```bash
pip install 'atomic-atlas[mcp-server]'
atomic-atlas-mcp                       # stdio MCP server
```

| Tool | Wraps |
|---|---|
| `list_atomics(vector?, technique?)` | `atomic-atlas list --json` |
| `read_atomic(path)` | parser.load |
| `recon_target(target, auth_header?)` | `atomic-atlas recon` |

`exec_atomic` over MCP is deferred to v0.2. It needs a profile/auth transport design that keeps credentials on the server side rather than in tool arguments.

## Configuring an MCP client

In your MCP-capable agent's config (Claude Desktop, Hermes, etc.):

```json
{
  "mcpServers": {
    "atomic-atlas": {
      "command": "atomic-atlas-mcp",
      "env": {
        "ATOMIC_ATLAS_ATOMICS_DIR": "/absolute/path/to/atomic-atlas/atomics"
      }
    }
  }
}
```

`ATOMIC_ATLAS_ATOMICS_DIR` is optional — defaults to the `atomics/` directory next to the installed package. Set it explicitly if your agent runs from a different working directory.

## Authorization

Both implementations must confirm with the user before running any test that has side effects on a real target. The CLI's `--authorized` flag is the underlying gate; the skill prompts the user before invoking exec; the MCP server defers to the calling agent's authorization UI (and in v0.2 will require it for `exec_atomic`).

Do not run atomics against systems you do not own or have written permission to test.
