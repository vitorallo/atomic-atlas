# Tasks: Agentic Targets

## v0.1 — completed

- [x] base.py — AtomicAtlasTarget(PromptTarget); `PYRIT_AVAILABLE` flag, `PyRITNotInstalledError`, `require_pyrit()` (PR1)
- [x] rag_corpus.py — RAGCorpusTarget (ChromaDB, Azure AI Search, HTTP ingest)
- [x] mcp_server.py — MCPServerTarget (`http_registry_stub` mode; renamed in PR2 to be honest about the placeholder)
- [x] tool_response.py — ToolResponseTarget (mock HTTP server)
- [x] document_upload.py — DocumentUploadTarget (OpenAI-compatible file API)
- [x] webhook.py — WebhookTarget (port-0 callback binding in PR2)
- [x] targets/__init__.py — lazy `__getattr__` so the subpackage imports without PyRIT (PR1)
- [x] All target modules: lazy PyRIT imports inside method bodies (PR1)
- [x] Seed payload JSON files for MCP, tool_response, webhook atomics
- [x] Smoke tests (tests/test_runner.py): vector→class mapping for all 5 adapter vectors, `UnsupportedVectorError`, `PyRITNotInstalledError`, setup-failure short-circuit, auth gate (PR3)

## v0.1 — completed (DVAA gap closures)

- [x] **DirectChatTarget** — wraps `pyrit.prompt_target.OpenAIChatTarget`; configured from target profile (`base_url`, `api_key`, `model`). Closes the gap where `direct_chat` raised `UnsupportedVectorError`. `direct_chat` added to `ADAPTER_VECTORS`. Lazy PyRIT import like the other targets. Live-verified against DVAA HelperBot.
- [x] **MCPJsonRpcTarget** — second mode `mcp_jsonrpc` on MCPServerTarget speaking real JSON-RPC 2.0 over HTTP. `tools/list` to enumerate, `tools/call` for crafted attacks, optional `tools/register`/`tools/unregister` with capability sniffing. Compatible with DVAA ToolBot, DVMCP, appsecco MCP lab. Live-verified against DVAA ToolBot 7010 (returned `read_file`, `write_file`, `execute`, `fetch_url` from `tools/list`).
- [x] PyRIT 0.13 API migration:
  - [x] `send_prompt_async(*, message: Message) -> list[Message]` (was `prompt_request: PromptRequestResponse`)
  - [x] `_build_orchestrator` → `_build_attack` using `pyrit.executor.attack.single_turn.PromptSendingAttack` (`PromptSendingOrchestrator` and `RedTeamingOrchestrator` were removed in PyRIT 0.13)
  - [x] Run loop now uses `attack.execute_async(parameters=AttackParameters(objective=...))` and parses `AttackResult.outcome`
  - [x] `SubStringScorer` API change accommodated (`category` → `categories`)
- [x] `tests/test_mcp_jsonrpc.py` — 3 tests with `httpx.MockTransport` for tools/list, tools/call success, tools/call error
- [x] DVAA smoke test verified live — `atomic-atlas runbook exec RB-DVAA-L1-01 --target http://localhost:7002/v1 --profile targets/dvaa_local.yaml --authorized` lands attack against HelperBot, DVAA `/stats` confirms `attacks: 3, successful: 3`

## v0.2 — broader target coverage

- [ ] **A2ATarget** — agent-to-agent message delivery. Targets DVAA Orchestrator/Worker (7020/7021), and the four ATLAS techniques requiring A2A scaffolding (T0109, T0111, T0115, T0116). `setup()` may register a peer agent card; `send_prompt_async()` POSTs the crafted A2A message; `cleanup()` deregisters.
- [ ] **WebFetchTarget** — agent that browses URLs. Inject content via a controlled web page; the agent's web_fetch tool retrieves it. Pairs with `AML.T0051.001 / web_fetch`.
- [ ] **EmailTarget** — inject via inbound email. Requires SMTP/IMAP scaffolding or a stub mailbox.
- [ ] **ComputerUseTarget** — content rendered on a screen the agent sees (ClickFix-style). Needs browser sandbox.
- [ ] **StatsScorer** (nice-to-have) — alternative to substring scoring; polls a target's metadata endpoint (e.g., DVAA's `/stats`) for an attack-success delta. Useful when chat responses are scripted/canned.
- [ ] Pinecone backend in RAGCorpusTarget
- [ ] Real MCP protocol adapter for the *registration* path (currently only `tools/call` is well-defined; spec-compliant remote tool registration is still in flux)
- [ ] HMAC signing as a documented mode in WebhookTarget._auth_headers()
- [ ] Azure DefaultAzureCredential support in `_auth_headers()`
