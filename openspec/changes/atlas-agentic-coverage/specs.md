# Specs: ATLAS Agentic Coverage Expansion

## Target technique × vector matrix

Rows = 21 agentic techniques. Columns = 12 vectors. `●` = v0.1 seeded. `○` = target for this change. `·` = not applicable.

| Technique | CHAT | SYSPROMPT | RAG | DOC | TOOL | MCP | WEB | HOOK | EMAIL | A2A | SCREEN | MODEL |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| T0051.000 Direct PI | ● | ○ | · | · | · | · | · | · | · | · | · | · |
| T0051.001 Indirect PI | · | · | ● | ● | ● | ● | ○ | ○ | ○ | ○ | ○ | · |
| T0053 Tool Invocation | ● | · | ○ | ○ | ● | · | · | · | · | · | · | · |
| T0065 Prompt Crafting | ● | · | · | · | · | · | · | · | · | · | · | · |
| T0086 Exfil via Tool | · | · | · | · | ○ | ● | · | ○ | · | · | · | · |
| T0093 Public App PI | · | · | · | · | · | · | · | ● | · | · | · | · |
| T0096 Memory Manip | ● | · | · | · | · | · | · | · | · | · | · | · |
| T0097 Memory Exfil | · | · | ○ | · | · | · | · | · | · | · | · | · |
| T0098 Cred Harvest | · | · | · | · | ● | ● | · | · | · | · | · | · |
| T0099 Tool Data Poison | · | · | · | · | ● | ○ | · | · | · | · | · | · |
| T0100 Computer Use | · | · | · | · | · | · | · | · | · | · | ○ | · |
| T0101 Comm Manip | · | · | · | · | · | · | · | ○ | ○ | · | · | · |
| T0104 Publish Poison | · | · | · | · | · | ● | · | · | · | · | · | · |
| T0109 Context Poison | · | · | · | · | · | ○ | · | · | · | ○ | · | · |
| T0110 Tool Poisoning | · | · | · | · | ○ | ○ | · | · | · | · | · | · |
| T0111 Instr Manip | ● | · | · | · | · | · | · | ○ | · | ○ | · | · |
| T0112 Resource Exhaust | · | · | · | · | · | ○ | · | · | · | ○ | · | · |
| T0113 Scope Violation | ● | · | · | · | · | · | · | · | · | · | · | · |
| T0114 Auth Bypass | ● | · | · | · | · | · | · | · | · | · | · | · |
| T0115 Indirect Exfil | · | · | · | · | · | ○ | · | · | · | ○ | · | · |
| T0116 Chain Hijack | · | · | · | · | · | · | · | · | · | ○ | · | · |

`●` = seeded in v0.1 (12 atomics)  
`○` = targeted in this change (~25 additional atomics)  
`·` = not applicable for this vector

## New targets required

| Vector | Target class | Status |
|---|---|---|
| `webhook` | WebhookTarget | v0.1 — in progress |
| `a2a_message` | A2ATarget | v0.2 |
| `computer_use` | ComputerUseTarget | v0.2 |
| `web_fetch` | WebFetchTarget | v0.2 |
| `email` | EmailTarget | v0.2 |

## Contribution workflow for new atomics

1. Check the matrix above for uncovered cells
2. Verify the technique + vector combination has a real case study in ATLAS
3. Write the atomic using `atomics/_TEMPLATE/vector_template.md`
4. Add payload seed to `payloads/`
5. Run `atomic-atlas validate atomics/AML.TXXXX/vector.md`
6. Open a PR — one atomic per PR

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
