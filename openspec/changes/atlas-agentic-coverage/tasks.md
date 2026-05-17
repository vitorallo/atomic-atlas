# Tasks: ATLAS Agentic Coverage Expansion

## PRD milestone mapping
This change delivers PRD v0.2 (coverage breadth) and v0.3 (community pipeline).

---

## v0.1 — Seeded (completed)
- [x] AML.T0051.000 / direct_chat
- [x] AML.T0051.001 / rag_corpus
- [x] AML.T0051.001 / document_upload
- [x] AML.T0051.001 / mcp_server
- [x] AML.T0051.001 / tool_response
- [x] AML.T0053 / tool_response
- [x] AML.T0065 / direct_chat
- [x] AML.T0086 / mcp_server
- [x] AML.T0093 / webhook
- [x] AML.T0098 / tool_response
- [x] AML.T0099 / tool_response
- [x] AML.T0104 / mcp_server

## v0.2 — Priority agentic expansion (next)
- [ ] AML.T0051.001 / webhook (requires WebhookTarget)
- [ ] AML.T0051.001 / a2a_message (requires A2ATarget)
- [ ] AML.T0051.001 / web_fetch (requires WebFetchTarget)
- [ ] AML.T0053 / rag_corpus
- [ ] AML.T0053 / direct_chat (additional variants)
- [ ] AML.T0086 / tool_response
- [ ] AML.T0086 / webhook
- [ ] AML.T0096 / direct_chat (Memory Manipulation)
- [ ] AML.T0097 / rag_corpus (Memory Exfiltration)
- [ ] AML.T0099 / mcp_server
- [ ] AML.T0101 / webhook (Communication Manipulation)
- [ ] AML.T0101 / email
- [ ] AML.T0109 / mcp_server (Context Poisoning)
- [ ] AML.T0109 / a2a_message
- [ ] AML.T0110 / tool_response (Tool Poisoning)
- [ ] AML.T0110 / mcp_server
- [ ] AML.T0111 / webhook (Instruction Manipulation)
- [ ] AML.T0111 / a2a_message
- [ ] AML.T0112 / mcp_server (Resource Exhaustion)
- [ ] AML.T0112 / a2a_message
- [ ] AML.T0115 / mcp_server (Indirect Exfiltration)
- [ ] AML.T0115 / a2a_message
- [ ] AML.T0116 / a2a_message (Chain Hijacking)

## v0.2 — Infrastructure for new vectors
- [ ] WebhookTarget implementation
- [ ] A2ATarget implementation
- [ ] WebFetchTarget implementation
- [ ] ComputerUseTarget implementation (ClickFix-style)
- [ ] EmailTarget implementation

## v0.3 — Coverage tooling
- [x] Auto-generate index.yaml from atomics directory (`scripts/generate_index.py`, `--check` for CI)
- [ ] Coverage badge in README (% of agentic techniques covered)
- [ ] GitHub Actions: validate new atomics on PR
- [ ] Coverage diff in PR description (which cells were added)
