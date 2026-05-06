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

### MCPServerTarget
**Modes**: `http_registry`  
**setup()**: POST `tool_payload` to `registry_url`; store `_registered_tool_id`  
**send_prompt_async()**: POST chat completions  
**cleanup()**: DELETE `{registry_url}/{_registered_tool_id}`

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
