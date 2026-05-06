# Tasks: Agentic Targets

## Completed
- [x] base.py — AtomicAtlasTarget(PromptTarget)
- [x] rag_corpus.py — RAGCorpusTarget (ChromaDB, Azure AI Search, HTTP ingest)
- [x] mcp_server.py — MCPServerTarget (http_registry mode)
- [x] tool_response.py — ToolResponseTarget (mock HTTP server)
- [x] document_upload.py — DocumentUploadTarget (OpenAI-compatible file API)
- [x] targets/__init__.py

## In progress
- [ ] webhook.py — WebhookTarget (POST crafted payload to inbound endpoint)

## Pending (v0.1)
- [ ] Create seed payload JSON files for MCP and tool_response atomics
- [ ] Unit tests for RAGCorpusTarget setup/cleanup mock
- [ ] Unit tests for ToolResponseTarget mock server start/stop

## Pending (v0.2)
- [ ] a2a.py — A2ATarget (agent-to-agent message delivery)
- [ ] Pinecone adapter in RAGCorpusTarget
- [ ] MCP server protocol adapter (replaces http_registry placeholder)
- [ ] HMAC signing in WebhookTarget._auth_headers()
- [ ] Azure DefaultAzureCredential support in _auth_headers()
