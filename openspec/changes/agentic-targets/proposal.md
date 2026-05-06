# Proposal: Agentic Targets

## Summary

Implement PyRIT `PromptTarget` subclasses for the agentic entry vectors that PyRIT does not natively cover. These are the core technical contribution of atomic-atlas — the layer that makes running ATLAS-keyed tests against RAG, MCP, tool response, document upload, and webhook vectors possible without hand-rolling the delivery each time.

## Problem

PyRIT's native targets send prompts to OpenAI-compatible chat endpoints. That's one of 12 entry vectors. The other 11 — particularly the agentic ones (RAG corpus, MCP server, tool response, document upload, webhook) — require different setup, delivery, and cleanup procedures that PyRIT doesn't model. Each new practitioner who wants to test these vectors has to build the adapter from scratch.

## Proposed solution

A set of `AtomicAtlasTarget(PromptTarget)` subclasses, one per vector type. Each implements:
- `setup()` — prepare the vector (inject document, start mock server, register tool)
- `send_prompt_async()` — deliver the trigger interaction to the agent chat interface
- `cleanup()` — restore the target to pre-test state

Authentication comes from the target profile YAML (env var references only; no credentials in code).

## Key design decisions

- **Auth in profiles, never in targets**: The target class reads auth from the adapter config dict, which is loaded from the profile YAML. Credentials are always env var references.
- **Backend abstraction within each target**: `RAGCorpusTarget` supports ChromaDB, Azure AI Search, and generic HTTP ingest via a `type` field in the adapter config. Adding a Pinecone adapter is a one-file addition.
- **No hard coupling to DVAA**: Targets work against any compliant backend. DVAA is the demo target; production targets use the same adapters with real credentials.

## Status

- [x] base.py (AtomicAtlasTarget)
- [x] rag_corpus.py (RAGCorpusTarget — ChromaDB + Azure AI Search + HTTP ingest)
- [x] mcp_server.py (MCPServerTarget — HTTP registry mode)
- [x] tool_response.py (ToolResponseTarget — mock HTTP server)
- [x] document_upload.py (DocumentUploadTarget — OpenAI-compatible file API)
- [ ] webhook.py (WebhookTarget)
- [ ] a2a.py (A2ATarget — v0.2)
