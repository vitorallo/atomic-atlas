# DVAA challenges → MITRE ATLAS mapping

This catalog maps the 22 published challenges in [DVAA (Damn Vulnerable AI Agent)](https://github.com/opena2a-org/damn-vulnerable-ai-agent) to MITRE ATLAS v5.6.0 techniques. Each challenge becomes one runbook under this directory; the runbook references atomic-atlas atomics that live in the technique-keyed `atomics/` catalog.

**Mapping principle:** ATLAS is canonical. Where a challenge fits an existing ATLAS technique cleanly, we use that ID. Where the closest ATLAS technique is a stretch, we use `UNCLASSIFIED.<slug>` rather than forcing a bad mapping. Multi-step challenges decompose into multiple atomics within one runbook.

ATLAS source: `data/atlas/ATLAS.yaml` (v5.6.0). Retrieval date: 2026-05-06.

## Coverage at a glance

| Bucket | Count |
|---|---:|
| DVAA challenges mapped | **22 / 22** |
| Runbooks shipped | **22** |
| Distinct ATLAS techniques exercised | **19** + 1 `UNCLASSIFIED.<slug>` |
| Atomics in catalog | **27** |
| ATLAS tactics traversed by the runbook set | **9 of 16** |

## Side-by-side mapping (22 / 22 challenges)

| DVAA ID | Challenge name | Category | Target agent (port) | Vector | ATLAS technique(s) | Runbook |
|---|---|---|---|---|---|---|
| L1-01 | Extract the System Prompt | data-exfiltration | HelperBot (7002) | direct_chat | **AML.T0084** Discover AI Agent Configuration | ✅ `L1-01__system-prompt-extraction.md` |
| L1-02 | API Key Leak | data-exfiltration | LegacyBot (7003) | direct_chat | **AML.T0084** + **AML.T0083** Credentials from AI Agent Configuration | ✅ `L1-02__api-key-leak.md` |
| L1-03 | Basic Prompt Injection | prompt-injection | HelperBot (7002) | direct_chat | **AML.T0051.000** LLM Prompt Injection: Direct | ✅ `L1-03__basic-prompt-injection.md` |
| L2-01 | Jailbreak via Roleplay | jailbreak | CodeBot (7004) | direct_chat | **AML.T0054** LLM Jailbreak | ✅ `L2-01__jailbreak-via-roleplay.md` |
| L2-02 | Context Window Manipulation | context-manipulation | HelperBot (7002) | direct_chat | **AML.T0080** AI Agent Context Poisoning | ✅ `L2-02__context-window-manipulation.md` |
| L2-03 | MCP Path Traversal | mcp-exploitation | ToolBot (7010) | mcp_server | **AML.T0086** Exfiltration via AI Agent Tool (path-traversal variant) | ✅ `L2-03__mcp-path-traversal.md` |
| L2-04 | Persistent Memory Injection | memory-injection | MemoryBot (7007) | direct_chat | **AML.T0080.000** Context Poisoning: Memory | ✅ `L2-04__persistent-memory-injection.md` |
| L2-05 | Memory Credential Extraction | memory-injection | MemoryBot (7007) | direct_chat | **AML.T0097** Memory Exfiltration | ✅ `L2-05__memory-credential-extraction.md` |
| L2-06 | Context Padding Attack | context-overflow | LongwindBot (7008) | direct_chat | **AML.T0112** Resource Exhaustion | ✅ `L2-06__context-padding-attack.md` |
| L2-07 | Safety Instruction Displacement | context-overflow | LongwindBot (7008) | direct_chat | **AML.T0112** + **AML.T0051.000** (chain) | ✅ `L2-07__safety-instruction-displacement.md` |
| L2-08 | Malicious Tool Registration | tool-registry-poisoning | PluginBot (7012) | mcp_server | **AML.T0104** Publish Poisoned AI Agent Tool | ✅ `L2-08__malicious-tool-registration.md` |
| L2-09 | Tool Call MITM | tool-mitm | ProxyBot (7013) | mcp_server | **AML.T0099** AI Agent Tool Data Poisoning | ✅ `L2-09__tool-call-mitm.md` |
| L3-01 | Chained Prompt Injection | prompt-injection | RAGBot (7005) | rag_corpus | **AML.T0051.001** Indirect PI | ✅ `L3-01__chained-prompt-injection.md` |
| L3-02 | SSRF via MCP | mcp-exploitation | ToolBot (7010) | mcp_server | **AML.T0086** (SSRF variant) | ✅ `L3-02__ssrf-via-mcp.md` |
| L3-03 | Self-Replicating Memory Entry | memory-injection | MemoryBot (7007) | direct_chat | **AML.T0080.000** + `UNCLASSIFIED.self-replicating-memory` (chain) | ✅ `L3-03__self-replicating-memory.md` |
| L3-04 | System Prompt Extraction via Context Pressure | context-overflow | LongwindBot (7008) | direct_chat | **AML.T0112** + **AML.T0084** (chain) | ✅ `L3-04__system-prompt-extraction-via-context-pressure.md` |
| L3-05 | Tool Typosquatting | tool-registry-poisoning | PluginBot (7012) | mcp_server | **AML.T0011.002** Poisoned AI Agent Tool | ✅ `L3-05__tool-typosquatting.md` |
| L3-06 | Tool Chain Data Exfiltration | tool-registry-poisoning | PluginBot (7012) | mcp_server | **AML.T0104** + **AML.T0086** (chain) | ✅ `L3-06__tool-chain-data-exfiltration.md` |
| L3-07 | Tool Shadowing | tool-mitm | ProxyBot (7013) | mcp_server | **AML.T0110** Tool Poisoning | ✅ `L3-07__tool-shadowing.md` |
| L3-08 | Traffic Redirection Attack | tool-mitm | ProxyBot (7013) | mcp_server | **AML.T0099** + **AML.T0108** AI Agent (as C2) (chain) | ✅ `L3-08__traffic-redirection-attack.md` |
| L4-01 | Compromise SecureBot | mixed | SecureBot (7001) | direct_chat | **AML.T0112** + **AML.T0054** + **AML.T0051.000** (3-step chain) | ✅ `L4-01__compromise-securebot.md` |
| L4-02 | Agent-to-Agent Attack Chain | agent-to-agent | Orchestrator (7020) / Worker (7021) | a2a_message | **AML.T0051.001** + **AML.T0086** + **AML.T0108** (3-step chain) | ✅ `L4-02__a2a-attack-chain.md` ⚠️ A2ATarget v0.2-pending |

## ATLAS technique exercise counts

How many DVAA challenges (across all 22) exercise each ATLAS technique. Counts include all primary + supporting mappings. A multi-step runbook contributes one count per technique it references.

| ATLAS technique | Tactic | Runbooks exercising it | Atomic shipped? |
|---|---|---:|:-:|
| **AML.T0011.002** Poisoned AI Agent Tool | Initial Access | 1 (L3-05) | ✅ |
| **AML.T0051.000** LLM Prompt Injection: Direct | Initial Access | 3 (L1-03, L2-07, L4-01) | ✅ |
| **AML.T0051.001** LLM Prompt Injection: Indirect | Initial Access | 2 (L3-01, L4-02) | ✅ (5 vectors) |
| **AML.T0054** LLM Jailbreak | Defense Evasion | 2 (L2-01, L4-01) | ✅ |
| **AML.T0080** AI Agent Context Poisoning | Persistence | 1 (L2-02) | ✅ |
| **AML.T0080.000** Context Poisoning: Memory | Persistence | 2 (L2-04, L3-03) | ✅ |
| **AML.T0083** Credentials from AI Agent Configuration | Credential Access | 1 (L1-02) | ✅ |
| **AML.T0084** Discover AI Agent Configuration | Discovery | 3 (L1-01, L1-02, L3-04) | ✅ |
| **AML.T0086** Exfiltration via AI Agent Tool | Exfiltration | 4 (L2-03, L3-02, L3-06, L4-02) | ✅ (3 vectors) |
| **AML.T0097** Memory Exfiltration | Exfiltration | 1 (L2-05) | ✅ |
| **AML.T0099** AI Agent Tool Data Poisoning | Defense Evasion | 2 (L2-09, L3-08) | ✅ (2 vectors) |
| **AML.T0104** Publish Poisoned AI Agent Tool | Persistence | 2 (L2-08, L3-06) | ✅ |
| **AML.T0108** AI Agent (as C2) | Command and Control | 2 (L3-08, L4-02) | ✅ (2 vectors) |
| **AML.T0110** Tool Poisoning | Defense Evasion | 1 (L3-07) | ✅ |
| **AML.T0112** Resource Exhaustion | Impact | 4 (L2-06, L2-07, L3-04, L4-01) | ✅ |
| `UNCLASSIFIED.self-replicating-memory` | (no current ATLAS technique) | 1 (L3-03) | ✅ |

**Distinct ATLAS techniques exercised by DVAA's 22 challenges:** 15 ATLAS-real + 1 unclassified = **16**.

## ATLAS tactics covered by DVAA runbooks

DVAA's 22 challenges traverse **9 of ATLAS v5.6.0's 16 tactics**:

| Tactic | DVAA runbook footprint |
|---|---|
| Initial Access | L1-03, L2-07, L3-05, L4-01, L4-02 |
| Persistence | L2-02, L2-04, L3-03, L2-08, L3-06 |
| Defense Evasion | L2-01, L2-07, L2-09, L3-07, L3-08, L4-01 |
| Credential Access | L1-02 |
| Discovery | L1-01, L1-02, L3-02, L3-04 |
| Collection | L2-05, L3-06 |
| Command and Control | L3-08, L4-02 |
| Exfiltration | L2-03, L2-05, L3-02, L3-06, L4-02 |
| Impact | L2-06, L2-07, L3-04, L4-01 |

Tactics not exercised by DVAA: Reconnaissance, Resource Development, ML Model Access, Execution, Privilege Escalation, ML Attack Staging — DVAA's design focuses on the offensive heart of agentic kill chains, not the breadth of ATLAS.

## Multi-step chains

Of the 22 runbooks, **6 are multi-step chains** that decompose into multiple atomics:

| Runbook | Chain |
|---|---|
| `RB-DVAA-L1-02` | T0084 → T0083 |
| `RB-DVAA-L2-07` | T0112 → T0051.000 |
| `RB-DVAA-L3-03` | T0080.000 → UNCLASSIFIED.self-replicating-memory |
| `RB-DVAA-L3-04` | T0112 → T0084 |
| `RB-DVAA-L3-06` | T0104 → T0086 |
| `RB-DVAA-L3-08` | T0099 → T0108 |
| `RB-DVAA-L4-01` | T0112 → T0054 → T0051.000 (3-step) |
| `RB-DVAA-L4-02` | T0051.001 → T0086 → T0108 (3-step, A2A) |

Single-atomic runbooks: 14. Multi-atomic chains: 8 (≥ 2 steps).

## Vector distribution

| Vector | Atomics | DVAA runbooks using it | Notes |
|---|---:|---:|---|
| `direct_chat` | 10 | 12 | Most-used vector; covers the chat-only attacks (L1-01–03, L2-01, L2-02, L2-04–07, L3-03, L3-04, L4-01) |
| `mcp_server` | 7 | 7 | Real MCP JSON-RPC; covers tool / registry / MITM attacks (L2-03, L2-08, L2-09, L3-02, L3-05–08) |
| `tool_response` | 4 | — | Pre-DVAA atomics from v0.1 seed catalog; not DVAA-driven |
| `a2a_message` | 3 | 1 | L4-02 only; A2ATarget v0.2-pending |
| `rag_corpus` | 1 | 1 | L3-01 |
| `document_upload` | 1 | — | v0.1 seed; not DVAA-driven |
| `webhook` | 1 | — | v0.1 seed; not DVAA-driven |

## Runbook execution status

22 / 22 runbooks pass `atomic-atlas runbook validate`. Live `atomic-atlas runbook exec` is operational against any target whose vectors have a CLI adapter (currently: `direct_chat`, `rag_corpus`, `document_upload`, `tool_response`, `mcp_server`, `webhook`). Runbooks referencing `a2a_message` (L4-02) require the v0.2 `A2ATarget` adapter; the agent runner skill provides a workaround for now.

## How this catalog grows

When a new DVAA release adds a challenge:

1. Add the row to the table above.
2. Decide ATLAS mapping (use real ID if it fits; `UNCLASSIFIED.<slug>` otherwise).
3. Write any missing atomics under `atomics/AML.TXXXX/<vector>.md` (or `atomics/unclassified/<slug>/<vector>.md`).
4. Write the runbook under `runbooks/dvaa/<id>__<slug>.md` referencing those atomics.
5. Validate: `atomic-atlas validate` (atomics) + `atomic-atlas runbook validate` (runbook refs).

When MITRE ATLAS publishes a technique that fits a previously-`UNCLASSIFIED` mapping (e.g., for self-replicating memory), retag the relevant atomic and update the row.

## Related docs

- [`docs/atlas-coverage.md`](../../docs/atlas-coverage.md) — full ATLAS v5.6.0 coverage stats (project-wide, not just DVAA-driven)
- [`runbooks/README.md`](../README.md) — runbook concept and authoring guide
- [`atomics/unclassified/README.md`](../../atomics/unclassified/README.md) — convention for atomics without an ATLAS mapping
- [`SPEC.md`](../../SPEC.md) — atomic format reference
