# Specs: Agentic Targets

## Base class contract

```python
class AtomicAtlasTarget(PromptTarget):
    atomic: AtomicTest
    profile: dict                    # full target profile
    _adapter_config: dict            # profile.adapters[vector]

    async def setup() -> None        # ABSTRACT
    async def cleanup() -> None      # ABSTRACT
    async def send_prompt_async(*, prompt_request) -> PromptRequestResponse  # ABSTRACT
    def _resolve_env(value: str) -> str   # expand ${VAR} refs
    def _auth_headers() -> dict[str, str] # build HTTP auth headers
```

## Target implementations

### RAGCorpusTarget
**Backends**: `chroma`, `azure_search`, `http_ingest`  
**setup()**: inject payload doc into RAG index; store `_injected_doc_id`  
**send_prompt_async()**: POST chat completions to `base_url/v1/chat/completions`  
**cleanup()**: delete doc by `_injected_doc_id`

ChromaDB adapter: POST to `/api/v1/collections/{collection}/add`  
Azure AI Search adapter: POST to `{endpoint}/indexes/{index}/docs/index?api-version=2023-11-01`  
HTTP ingest: POST to `adapter_config.ingest_url`; DELETE to `adapter_config.delete_url`

### DirectChatTarget
**Modes**: `openai_compatible`  
Wraps `pyrit.prompt_target.OpenAIChatTarget` with config from the target profile (`base_url`, `api_key`, `model`). Closes the gap where `direct_chat` was `UnsupportedVectorError` and forced users into the agent runner for chat-only atomics. Works against any OpenAI-compatible endpoint: DVAA HelperBot/LegacyBot/etc., production Azure OpenAI agents, LiteLLM proxies, vLLM, Ollama-OpenAI shim.  
**setup()**: no-op (chat is stateless from the target's POV).  
**send_prompt_async()**: delegate to the wrapped `OpenAIChatTarget`.  
**cleanup()**: no-op.

### MCPServerTarget
**Modes**: `http_registry_stub`, `mcp_jsonrpc`  

`http_registry_stub` (v0.1 placeholder):  
**setup()**: POST `tool_payload` to `registry_url`; store `_registered_tool_id`  
**send_prompt_async()**: POST chat completions  
**cleanup()**: DELETE `{registry_url}/{_registered_tool_id}`

`mcp_jsonrpc` (v0.1 — real MCP):  
Speaks JSON-RPC 2.0 over HTTP. Targets DVAA's ToolBot/PluginBot/DataBot/ProxyBot, [DVMCP](https://github.com/harishsg993010/damn-vulnerable-MCP-server), the [appsecco MCP lab](https://github.com/appsecco/vulnerable-mcp-servers-lab), and any spec-compliant MCP server reachable over HTTP.  
**setup()**: `POST /` with `{"jsonrpc":"2.0","method":"tools/list"}`; store baseline tool list. If the atomic specifies `tool_payload` and the server supports `tools/register`, register a poisoned tool and store its id for cleanup.  
**send_prompt_async()**: `POST /` with `{"jsonrpc":"2.0","method":"tools/call","params":{"name":<target_tool>,"arguments":<attack_args>}}`. Returns the tool's response text as the prompt response (so substring scorers can match exfil/RCE markers).  
**cleanup()**: if a tool was registered, deregister via `tools/unregister` (when supported); otherwise no-op.

### ToolResponseTarget
**setup()**: start `HTTPServer` on `localhost:{port}`; serve `poisoned_response` as JSON for GET and POST  
**send_prompt_async()**: POST chat completions (agent will call the mock server when it processes the trigger)  
**cleanup()**: `server.shutdown()`

### DocumentUploadTarget
**setup()**: POST file to `upload_url` (multipart); store `_uploaded_file_id`  
**send_prompt_async()**: POST chat completions with `attachments: [{file_id, tools}]`  
**cleanup()**: DELETE `{delete_url}`

### WebhookTarget (pending)
**setup()**: start callback listener  
**send_prompt_async()**: POST crafted webhook JSON to target inbound endpoint  
**cleanup()**: stop listener

## Target profile schema

```yaml
base_url: <agent chat base URL>
adapters:
  <vector>:
    type: <backend type>
    # backend-specific fields
    api_key: ${ENV_VAR}         # or bearer_token, azure_default_credential
```

## Auth schemes

| Scheme | Profile field | HTTP effect |
|---|---|---|
| API key | `api_key: ${VAR}` | `Authorization: Bearer <key>` |
| Bearer token | `auth: {type: bearer, token: ${VAR}}` | `Authorization: Bearer <token>` |
| Azure DefaultAzureCredential | `auth: {type: azure_default}` | Token via `azure.identity` |
| API key header | `auth: {type: api_key, header: X-API-Key, key: ${VAR}}` | `X-API-Key: <key>` |
| HMAC | `auth: {type: hmac, secret: ${VAR}}` | `X-Hub-Signature-256: sha256=<sig>` |

## Dependency

```
pyrit>=0.5.0
httpx>=0.27.0
```
