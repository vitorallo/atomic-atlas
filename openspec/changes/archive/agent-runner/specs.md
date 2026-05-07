# Specs: Agent Runner

## Architectural contract

The atomic-atlas CLI is the **interface** an agent runner must wrap. Both the Claude Code skill and the MCP server are higher layers over the CLI; neither re-implements parsing, target instantiation, orchestration, scoring, or result-emission.

```
+-----------------------------------------------+
| Agent runner (skill / MCP server)             |
|   reasoning: pick, adapt, evaluate, chain     |
+-----------------------------------------------+
                     |
                     v   (subprocess / module import)
+-----------------------------------------------+
| atomic-atlas CLI                              |
|   list / recon / exec / report / validate     |
+-----------------------------------------------+
                     |
                     v   (Python imports)
+-----------------------------------------------+
| atomic_atlas library                          |
|   parser, runner, targets, recon, reporters   |
+-----------------------------------------------+
                     |
                     v   (optional: only for exec)
+-----------------------------------------------+
| PyRIT (orchestrator extra)                    |
+-----------------------------------------------+
```

## CLI primitives the agent must use

| CLI command | Purpose for the agent |
|---|---|
| `atomic-atlas list [--vector V] [--technique T] [--json]` | Discover atomics in the catalog |
| `atomic-atlas recon --target URL` | Fingerprint the target's exposed entry vectors |
| `atomic-atlas exec ATOMIC --target URL --profile P --authorized` | Execute an atomic; emits results.json |
| `atomic-atlas report --input results.json --format navigator|coverage|markdown` | Generate output for the engagement report |
| `atomic-atlas validate [PATH]` | Validate atomic frontmatter (used when the agent writes a new payload variant) |

## Result file shape (results.json)

The agent reads results.json after `exec`. Schema:

```json
[
  {
    "atomic_path": "atomics/AML.T0051.001/rag_corpus.md",
    "atlas_technique": "AML.T0051.001",
    "interaction_vector": "rag_corpus",
    "guid": "...",
    "total_runs": 5,
    "successes": 3,
    "failures": 2,
    "errors": 0,
    "duration_seconds": 12.7,
    "run_details": [{"run": 1, "success": true, "response_preview": "..."}, ...]
  }
]
```

`exec` appends to results.json across invocations, so the agent can run multiple atomics into the same file, then call `report --input results.json` once.

## When the agent is allowed to bypass the CLI

The agent SHOULD always start with `atomic-atlas exec`. It MAY bypass the CLI only in these cases, and MUST record the bypass in the final report:

1. **`UnsupportedVectorError` raised by exec** (vectors without CLI adapters: `direct_chat`, `system_prompt`, `web_fetch`, `email`, `a2a_message`, `computer_use`, `model_api`). The agent delivers via the appropriate channel directly.
2. **Backend mismatch.** The target's RAG / MCP / upload backend isn't covered by any CLI adapter. The agent uses the target's native API for that step, then runs the chat trigger via the CLI (or via direct HTTP).
3. **Semantic scoring required.** `SubStringScorer` flagged failure but the agent's own evaluation of `## Success criteria` against the response transcript indicates success (or vice versa).
4. **Adaptive payload generation.** The agent writes a tailored payload variant to the atomic's `payloads/` directory and re-runs via the CLI.

In all four cases, the bypass MUST be reproducible — the agent records the exact commands run and inputs used.

## Authorization gate

The CLI requires `--authorized` per `exec`. The agent runner MUST confirm with the user before passing this flag. The skill does this in its first turn ("Confirm you have written authorization to test [target URL]?"); the MCP server requires the calling agent to surface authorization to the user before invoking exec_atomic (v0.2).

## Claude Code skill (v0.1 — implemented)

The skill at `skill/atomic-atlas.md` MUST:
- Treat the CLI as the primary execution path (steps 1–7 in the skill body).
- Document the four bypass conditions explicitly in a "Fallback: manual delivery" section.
- Include an authorization-prompt step before any `exec` call.
- Provide a chaining policy: T0051.001 success → consider T0053 → consider T0086.

## MCP server (v0.1 — read-only stub)

The MCP server at `mcp/server.py` MUST:
- Run without PyRIT installed (uses parser.load_all and recon.recon, neither of which need PyRIT).
- Expose three tools:

```python
list_atomics(vector: str | None = None, technique: str | None = None) -> list[dict]
    # Returns the same shape as `atomic-atlas list --json`

read_atomic(path: str) -> dict
    # Returns frontmatter + sections for a specific atomic.
    # `path` is relative to the atomics/ directory (e.g., "AML.T0051.001/rag_corpus.md").

recon_target(target: str, auth_header: str | None = None) -> dict
    # Returns recon results: detected vectors, guardrails, suggested techniques.
```

- All three tools are read-only and side-effect-free.
- `exec_atomic` is **out of scope for v0.1** — deferred to v0.2.

## MCP server (v0.2 — exec, deferred)

`exec_atomic(atomic_path, target, profile_yaml, authorized=True, runs=None) -> dict` will execute an atomic. The challenge in MCP is profile/auth: the calling agent must transmit credentials safely. Resolution path: the MCP server reads `${ENV_VAR}` references in the profile and resolves them from its own process env (never from the MCP tool args), so secrets stay on the MCP server's host. Specified in a follow-up change.

## Out of scope for this change

- Real MCP protocol implementation in `MCPServerTarget` (PRD open question #4 — separate concern).
- A2ATarget (v0.2 — `agentic-targets` extension).
- Hermes agent profile / system prompt (v0.2).
