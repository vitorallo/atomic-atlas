# Tasks: Lobster (vulnerable-agent)

## v0.2 — implementation

### Scaffolding

- [ ] `examples/lobster/pyproject.toml` (langgraph, langchain-openai, langchain-chroma, langchain-mcp-adapters, fastapi, uvicorn, httpx)
- [ ] `examples/lobster/Dockerfile`
- [ ] `examples/lobster/docker-compose.yml` — lobster + chromadb sidecar; binds `127.0.0.1` by default
- [ ] `examples/lobster/README.md` — Lobster banner; safety callout; full ATLAS coverage table; bring-up; how to add a new vulnerability + atomic together
- [ ] `examples/lobster/target_profile.yaml`

### Agent core

- [ ] `src/main.py` — FastAPI app + LangGraph build + `X-Lobster: do-not-deploy` middleware + bind-all guard
- [ ] `src/graph.py` — LangGraph `StateGraph` (input → llm → tools → memory → output); no `interrupt_before`; no recursion limit
- [ ] `src/system_prompt.py` — system prompt with **fake creds** for T0098 + magic admin phrase for T0111
- [ ] `src/tools.py` — `external_lookup`, `send_email`, `lookup_internal`, `admin_action`, dynamic-tool dispatcher
- [ ] `src/rag.py` — Chroma init; `ingest`, `query`, `delete`; no provenance markers on retrieved content
- [ ] `src/mcp_stub.py` — MCP registry stub: `POST/GET/DELETE /mcp/tools`; description/implementation unbound (enables T0110)
- [ ] `src/memory.py` — `read_memory`/`write_memory` tools; cross-conversation read by guessing IDs (T0096, T0097)
- [ ] `src/webhook.py` — `/inbound`; free-text fields fed to the LLM; optional HMAC via `LOBSTER_WEBHOOK_HMAC`

### ATLAS technique vulnerabilities (one task per technique)

Each task is "wire the vulnerability described in specs.md, tag the site with `# ATLAS: AML.TXXXX`, and confirm a corresponding atomic targets it." If no atomic exists yet for a technique, write one as part of the same task.

- [ ] T0051.000 — Direct Prompt Injection (atomic exists; verify)
- [ ] T0051.001 — Indirect Prompt Injection (atomic exists; verify across rag/doc/tool/mcp/webhook)
- [ ] T0053 — Agent Tool Invocation (atomic exists; verify)
- [ ] T0065 — LLM Prompt Crafting (atomic exists; verify)
- [ ] T0086 — Exfiltration via Agent Tool (atomic exists for mcp; add tool-vector atomic if missing)
- [ ] T0093 — Public-Facing App PI (atomic exists; verify)
- [ ] T0096 — Memory Manipulation — **new atomic** required
- [ ] T0097 — Memory Exfiltration — **new atomic** required
- [ ] T0098 — Tool Credential Harvesting (atomic exists; verify)
- [ ] T0099 — Tool Data Poisoning (atomic exists; verify)
- [ ] T0101 — Communication Manipulation — **new atomic** required
- [ ] T0104 — Publish Poisoned AI Agent Tool (atomic exists; verify)
- [ ] T0109 — Context Poisoning — **new atomic** required
- [ ] T0110 — Tool Poisoning — **new atomic** required
- [ ] T0111 — Instruction Manipulation — **new atomic** required
- [ ] T0112 — Resource Exhaustion — **new atomic** required
- [ ] T0113 — Scope Violation — **new atomic** required
- [ ] T0114 — Authorization Bypass — **new atomic** required

### Verification

- [ ] All listed atomics pass against Lobster locally
- [ ] GitHub Actions workflow: spin up Lobster, run all atomics, assert per-technique success rate
- [ ] Coverage check: every `# ATLAS: AML.TXXXX` tag in Lobster source has at least one atomic targeting it; CI fails on mismatch
- [ ] Update `targets/dvaa_local.yaml` to remain valid alongside (Lobster is the new default; DVAA is the alternative)
- [ ] Update README + docs/quickstart.md + docs/targets.md: Lobster is the default demo target; DVAA is the elaborate alternative
- [ ] Update PRD.md milestone v0.2 to reflect Lobster as a deliverable

### Safety

- [ ] `X-Lobster: do-not-deploy` middleware
- [ ] docker-compose binds `127.0.0.1` by default; `LOBSTER_BIND_ALL=1` to override with startup confirmation
- [ ] `external_lookup` URL allowlist (localhost + RFC1918 + configurable callback domain)
- [ ] README "do not deploy on public infrastructure" callout

## v0.3 — extensions

- [ ] **A2A vector + 4 deferred techniques.** Add `/.well-known/agent-card` + `/a2a/inbox`; implement T0115, T0116. First open A2A target.
- [ ] **Persistent memory** for T0102 (cross-restart memory persistence attack).
- [ ] **Computer Use** vector for T0100 — separate sandbox scaffolding.
- [ ] **`LOBSTER_HARDEN=AML.T0086,...`** env: turn specific vulnerabilities off — test bed for mitigation atomics.
- [ ] **Sibling SDK examples.** `examples/lobster_openai_sdk/` and `examples/lobster_anthropic/`. Demonstrates atomic-atlas runs against multiple SDK families.
- [ ] **Fully offline mode** with HF Phi-3-mini for keyless demos.

## Open decisions to lock before starting v0.2

- **LLM backing:** `ChatOpenAI` default + documented Anthropic swap (recommended), vs. abstract behind config knob.
- **MCP client:** `langchain-mcp-adapters` directly (recommended), vs. thin wrapper.
- **Webhook signing:** ship optional HMAC mode via env (recommended), vs. unsigned-only.
- **CI threshold:** what success rate per technique counts as "Lobster is still vulnerable to T0086"? Recommendation: ≥ 1/5 runs succeed counts as still-vulnerable; < 1/5 means a regression that broke the demo.
