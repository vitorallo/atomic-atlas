# Specs: ATLAS Agentic Coverage Expansion

Target framework: **MITRE ATLAS v5.6.0** (downloaded 2026-05-06; see `data/atlas/MANIFEST.md`).

## Phantom IDs removed

The prior tracker listed `T0113`, `T0114`, `T0115`, `T0116`. **These IDs do not exist in ATLAS v5.6.0** — the highest published technique number is `T0112`. They were forward-looking placeholders. Re-mapping:

| Phantom ID | Was tracker name | Re-mapped to |
|---|---|---|
| T0113 | Scope Violation | `UNCLASSIFIED.scope-violation` (no current ATLAS technique covers "agent acts outside its declared role") |
| T0114 | Authorization Bypass | `UNCLASSIFIED.authorization-bypass` (no current ATLAS technique for "trick agent into authorizing an action") |
| T0115 | Indirect Exfiltration | covered by **AML.T0086 Exfiltration via AI Agent Tool** through the `a2a_message` vector — not a new technique |
| T0116 | Chain Hijacking | `UNCLASSIFIED.chain-hijack-a2a` (no current technique for "hijack a multi-agent plan mid-flow") |

The unclassified atomics live under `atomics/unclassified/<slug>/`. See `atomics/unclassified/README.md`.

## Target coverage matrix (v5.6.0-aligned)

Rows = 34 agentic techniques in ATLAS v5.6.0 we target. Columns = 12 vectors. `●` = v0.1 seeded. `○` = v0.2 target. `·` = not applicable.

### Previously tracked (17 verified present in v5.6.0)

| Technique | CHAT | SYSPROMPT | RAG | DOC | TOOL | MCP | WEB | HOOK | EMAIL | A2A | SCREEN | MODEL |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| T0051.000 LLM Prompt Injection: Direct | ● | ○ | · | · | · | · | · | · | · | · | · | · |
| T0051.001 LLM Prompt Injection: Indirect | · | · | ● | ● | ● | ● | ○ | ○ | ○ | ○ | ○ | · |
| T0053 LLM Plugin Compromise / Agent Tool Invocation | ● | · | ○ | ○ | ● | · | · | · | · | · | · | · |
| T0065 LLM Prompt Crafting | ● | · | · | · | · | · | · | · | · | · | · | · |
| T0086 Exfiltration via AI Agent Tool | · | · | · | · | ○ | ● | · | ○ | · | ○ | · | · |
| T0093 Prompt Infiltration via Public-Facing App | · | · | · | · | · | · | · | ● | · | · | · | · |
| T0096 Memory Manipulation | ● | · | · | · | · | · | · | · | · | · | · | · |
| T0097 Memory Exfiltration | · | · | ○ | · | · | · | · | · | · | · | · | · |
| T0098 AI Agent Tool Credential Harvesting | · | · | · | · | ● | ● | · | · | · | · | · | · |
| T0099 AI Agent Tool Data Poisoning | · | · | · | · | ● | ○ | · | · | · | · | · | · |
| T0100 Computer Use | · | · | · | · | · | · | · | · | · | · | ○ | · |
| T0101 Communication Manipulation | · | · | · | · | · | · | · | ○ | ○ | · | · | · |
| T0104 Publish Poisoned AI Agent Tool | · | · | · | · | · | ● | · | · | · | · | · | · |
| T0109 Context Poisoning | · | · | · | · | · | ○ | · | · | · | ○ | · | · |
| T0110 Tool Poisoning | · | · | · | · | ○ | ○ | · | · | · | · | · | · |
| T0111 Instruction Manipulation | ● | · | · | · | · | · | · | ○ | · | ○ | · | · |
| T0112 Resource Exhaustion | · | · | · | · | · | ○ | · | · | · | ○ | · | · |

### NEW agentic techniques in v5.6.0 (added in this change)

| Technique | Tactic | Vectors targeted |
|---|---|---|
| T0002.002 AI Agent Configuration | Reconnaissance | `web_fetch`, `direct_chat` |
| T0010.005 Acquire AI Agent Tool | Resource Development | (build-time; recon-only atomics) |
| T0011.002 Poisoned AI Agent Tool | Initial Access | `mcp_server`, `tool_response` |
| T0034.002 Agentic Resource Consumption | Impact | `mcp_server`, `a2a_message`, `tool_response` |
| T0064 Gather RAG-Indexed Targets | Reconnaissance | `direct_chat`, `web_fetch` |
| T0066 Retrieval Content Crafting | Resource Development | `rag_corpus`, `document_upload` |
| T0070 RAG Poisoning | Persistence | `rag_corpus`, `document_upload` |
| T0071 False RAG Entry Injection | Defense Evasion | `rag_corpus` |
| T0080 AI Agent Context Poisoning | Persistence | `mcp_server`, `tool_response`, `a2a_message` |
| T0080.000 AI Agent Context Poisoning: Memory | Persistence | `direct_chat`, `tool_response` |
| T0081 Modify AI Agent Configuration | Persistence | `mcp_server`, `direct_chat` |
| T0082 RAG Credential Harvesting | Credential Access | `rag_corpus`, `direct_chat` |
| T0083 Credentials from AI Agent Configuration | Credential Access | `direct_chat`, `mcp_server` |
| T0084 Discover AI Agent Configuration | Discovery | `direct_chat`, `mcp_server` |
| T0084.001 Discover AI Agent Tool Definitions | Discovery | `mcp_server`, `direct_chat` |
| T0085.000 Collection: RAG Databases | Collection | `rag_corpus`, `direct_chat` |
| T0085.001 Collection: AI Agent Tools | Collection | `mcp_server`, `direct_chat` |
| T0103 Deploy AI Agent | Execution | (adversary-launched; out-of-band) |
| T0108 AI Agent (as C2) | Command and Control | `a2a_message`, `mcp_server` |
| T0112.000 Resource Exhaustion: Local AI Agent | Impact | `computer_use`, `tool_response` |

## Coverage targets

- **v0.1** (current): 12 atomics across 9 techniques (`●` cells above)
- **v0.2** (post-keynote): expand to ~40 atomics covering all 34 techniques in the matrix above
- **v0.3** (community pipeline): unrestricted growth via PR contribution

## Vendored ATLAS data

The repo ships `data/atlas/ATLAS.yaml` (the v5.6.0 framework) so contributors can:
- Validate that a proposed technique ID exists before opening a PR
- Refresh this matrix when ATLAS publishes new versions
- Keep the project decoupled from network availability of `atlas.mitre.org`

A future task: a small `atomic-atlas atlas-refresh` CLI command that fetches the latest `ATLAS.yaml`, diffs against the vendored copy, and reports new agentic techniques to add to this matrix.

## New target classes required

| Vector | Target class | Status |
|---|---|---|
| `direct_chat` | DirectChatTarget | v0.1 (just landed) |
| `mcp_server` (real MCP) | MCPJsonRpcTarget | v0.1 — pending |
| `webhook` | WebhookTarget | ✅ v0.1 |
| `a2a_message` | A2ATarget | v0.2 |
| `computer_use` | ComputerUseTarget | v0.2 |
| `web_fetch` | WebFetchTarget | v0.2 |
| `email` | EmailTarget | v0.2 |

## Contribution workflow for new atomics

1. Check the matrix above for uncovered cells.
2. Verify the technique exists in `data/atlas/ATLAS.yaml`. If not, place under `atomics/unclassified/<slug>/`.
3. Copy `atomics/_TEMPLATE/vector_template.md`, rename, fill in.
4. Add payload seed(s) to `payloads/` if needed.
5. Run `atomic-atlas validate atomics/<technique>/<vector>.md`.
6. Open a PR — one atomic per PR.

## index.yaml schema (auto-generated)

```yaml
version: 1
generated: 2026-05-06
atomics:
  - technique: AML.T0051.001
    vector: rag_corpus
    path: atomics/AML.T0051.001/rag_corpus.md
    guid: 3f8c2d1a-4b5e-4a6f-9c7d-8e2f1b3a5c9e
    display_name: Indirect Prompt Injection
    runs: 5
```
