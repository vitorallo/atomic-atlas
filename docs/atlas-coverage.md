# ATLAS coverage

Project-wide stats for atomic-atlas's coverage of MITRE ATLAS v5.6.0. Updated 2026-05-17.

## Headline numbers

| Metric | Value |
|---|---:|
| ATLAS framework version | **v5.6.0** (released 2026-05-04) |
| Total ATLAS techniques (incl. sub-techniques) | 170 |
| Agentic-relevant techniques in ATLAS v5.6.0 | 51 (29 high-confidence + 22 "probably") |
| Atomics shipped | **27** |
| Runbooks shipped | **22** |
| Distinct ATLAS techniques covered by atomics | **19** |
| `UNCLASSIFIED.<slug>` atomics | **1** |
| ATLAS tactics traversed by runbooks | **9 of 16** |
| Coverage of high-confidence agentic ATLAS techniques | **12 / 29 = 41%** |
| Coverage of all agentic-relevant ATLAS techniques | **15 / 51 = 29%** |

The "high-confidence agentic" denominator is what most practitioner-facing claims should use — those are the 29 techniques in ATLAS v5.6.0 that are explicitly about agent behavior (RAG, MCP, tool use, memory, A2A, agent configuration). The "all agentic-relevant" denominator (51) includes 22 techniques that touch agents only tangentially (jailbreak, drive-by, sandbox-escape applied to agent contexts).

## Atomics by ATLAS technique

20 distinct technique IDs (19 ATLAS + 1 unclassified). Some techniques are covered across multiple vectors.

| Technique | Tactic | Vectors covered | Atomic count |
|---|---|---|---:|
| **AML.T0011.002** Poisoned AI Agent Tool | Initial Access | mcp_server | 1 |
| **AML.T0051.000** LLM Prompt Injection: Direct | Initial Access | direct_chat | 1 |
| **AML.T0051.001** LLM Prompt Injection: Indirect | Initial Access | rag_corpus, document_upload, mcp_server, tool_response, a2a_message | **5** |
| **AML.T0053** AI Agent Tool Invocation | Execution | tool_response | 1 |
| **AML.T0054** LLM Jailbreak | Defense Evasion | direct_chat | 1 |
| **AML.T0065** LLM Prompt Crafting | Resource Development | direct_chat | 1 |
| **AML.T0080** AI Agent Context Poisoning | Persistence | direct_chat | 1 |
| **AML.T0080.000** Context Poisoning: Memory | Persistence | direct_chat | 1 |
| **AML.T0083** Credentials from AI Agent Configuration | Credential Access | direct_chat | 1 |
| **AML.T0084** Discover AI Agent Configuration | Discovery | direct_chat | 1 |
| **AML.T0086** Exfiltration via AI Agent Tool | Exfiltration | mcp_server, a2a_message | 2 |
| **AML.T0093** Prompt Infiltration via Public-Facing Application | Initial Access | webhook | 1 |
| **AML.T0097** Memory Exfiltration | Exfiltration | direct_chat | 1 |
| **AML.T0098** AI Agent Tool Credential Harvesting | Credential Access | tool_response | 1 |
| **AML.T0099** AI Agent Tool Data Poisoning | Defense Evasion | tool_response, mcp_server | 2 |
| **AML.T0104** Publish Poisoned AI Agent Tool | Persistence | mcp_server | 1 |
| **AML.T0108** AI Agent (as C2) | Command and Control | mcp_server, a2a_message | 2 |
| **AML.T0110** Tool Poisoning | Defense Evasion | mcp_server | 1 |
| **AML.T0112** Resource Exhaustion | Impact | direct_chat | 1 |
| `UNCLASSIFIED.self-replicating-memory` | (no current ATLAS technique) | direct_chat | 1 |

**Totals:** 19 ATLAS-real techniques + 1 `UNCLASSIFIED.<slug>` = **20 distinct technique IDs**, 27 atomics across **7 of 12 interaction vectors**.

## Atomics by interaction vector

| Vector | Count | Status |
|---|---:|---|
| `direct_chat` | 10 | ✅ DirectChatTarget shipped (v0.1) |
| `mcp_server` | 7 | ✅ MCPServerTarget with `mcp_jsonrpc` mode (v0.1) |
| `tool_response` | 4 | ✅ ToolResponseTarget (v0.1) |
| `a2a_message` | 3 | ⚠️ A2ATarget v0.2-pending |
| `rag_corpus` | 1 | ✅ RAGCorpusTarget (v0.1) |
| `document_upload` | 1 | ✅ DocumentUploadTarget (v0.1) |
| `webhook` | 1 | ✅ WebhookTarget (v0.1) |
| `system_prompt`, `web_fetch`, `email`, `computer_use`, `model_api` | 0 | Reachable via agent runner only; no CLI adapter |

## Runbooks

| Runbook category | Count | Notes |
|---|---:|---|
| `dvaa_challenge` | 22 | Full DVAA v0.8.0 catalog mapped (`runbooks/dvaa/`) |
| `kill_chain` | 0 | Planned: indirect-pi-to-tool-exfil, rag-poison-to-cred-harvest, mcp-tool-poison-to-c2 |
| `engagement` | 0 | Planned: customer-support-agent-baseline, mcp-deployed-agent-baseline |
| **Total runbooks** | **22** | |

Of the 22 DVAA runbooks, **8 are multi-step chains** (≥2 atomics with `depends_on`), the most ambitious being `RB-DVAA-L4-01` and `RB-DVAA-L4-02` (3-step chains spanning 3 ATLAS tactics each).

## ATLAS tactic coverage

ATLAS v5.6.0 has 16 tactics. atomic-atlas's runbooks traverse **9** of them.

| Tactic | Atomic count | Runbook count | Status |
|---|---:|---:|---|
| Reconnaissance | 0 | 0 | Targeted in v0.2 — T0002.002, T0064 |
| Resource Development | 1 (T0065) | 0 | Targeted in v0.2 — T0010.005, T0066 |
| Initial Access | 8 (T0051.000 + T0051.001 × 5 + T0011.002 + T0093) | 6 | ✅ Strong coverage |
| ML Model Access | 0 | 0 | Out of v0.2 scope |
| Execution | 1 (T0053) | 0 | Targeted in v0.2 — T0103 |
| Persistence | 4 (T0080, T0080.000, T0104, plus the unclassified) | 6 | ✅ Strong coverage |
| Privilege Escalation | 0 | 0 | Not currently targeted |
| Defense Evasion | 4 (T0054, T0099 × 2, T0110) | 6 | ✅ Strong coverage |
| Credential Access | 2 (T0083, T0098) | 1 | ⚠️ Targeted in v0.2 — T0082 |
| Discovery | 1 (T0084) | 4 | Targeted in v0.2 — T0084.001 |
| Collection | 0 | 2 | Targeted in v0.2 — T0085.000, T0085.001 |
| Command and Control | 2 (T0108 × 2) | 2 | ✅ |
| ML Attack Staging | 0 | 0 | Out of v0.2 scope |
| Exfiltration | 3 (T0086 × 2, T0097) | 5 | ✅ Strong coverage |
| Impact | 1 (T0112) | 4 | ✅ |

## Coverage gaps

Tracked in `openspec/changes/atlas-agentic-coverage/specs.md`. The 17 ATLAS-v5.6.0 techniques flagged for catalog expansion (not yet seeded):

**Reconnaissance / Discovery layer:** T0002.002, T0064, T0084.001  
**Resource Development:** T0010.005, T0066  
**Persistence (RAG/memory layer):** T0070, T0071, T0081  
**Credential Access:** T0082  
**Collection:** T0085.000, T0085.001  
**Execution:** T0103  
**Impact:** T0034.002, T0112.000

Plus the 5 vectors without CLI adapters today: `system_prompt`, `web_fetch`, `email`, `computer_use`, `model_api` — exercised via the agent runner only.

## Methodology — how we count

- **"Distinct ATLAS techniques covered"** counts unique `atlas_technique` values across all atomic files in `atomics/` (excluding payload files and unclassified entries).
- **"Atomic count"** is the file count, where each file is one `(technique × vector)` cell. A technique covered across multiple vectors contributes multiple atomic counts (e.g., `T0051.001` covers 5 vectors, contributes 5).
- **"Runbook count"** is the file count under `runbooks/`. A multi-step runbook still counts as one runbook regardless of how many atomics it composes.
- **"Coverage %"** is `(distinct ATLAS techniques covered) / (denominator)`. We report two denominators: the 29 high-confidence agentic techniques (the meaningful denominator for practitioner claims) and the 51 total agentic-relevant techniques (the broadest framing).

## Reproducing these numbers

```bash
# Atomic counts by technique and vector
atomic-atlas list --json | jq 'group_by(.atlas_technique) | map({technique: .[0].atlas_technique, atomics: length, vectors: [.[].interaction_vector] | sort})'

# Runbook counts by type and tactic
atomic-atlas runbook list --json | jq 'group_by(.runbook_type) | map({type: .[0].runbook_type, count: length})'

# Cross-check against the canonical ATLAS data
python3 -c "
import json
agentic = json.load(open('data/atlas/agentic_techniques_extracted.json'))
print(f'Total agentic in ATLAS v5.6.0: {len(agentic)}')
print(f'High confidence: {sum(1 for t in agentic if t.get(\"agentic\") == \"yes\")}')
"
```

## Related docs

- [`runbooks/dvaa/README.md`](../runbooks/dvaa/README.md) — DVAA-specific mapping (22-row side-by-side table)
- [`openspec/changes/atlas-agentic-coverage/specs.md`](../openspec/changes/atlas-agentic-coverage/specs.md) — v0.2 catalog-expansion targets and the technique × vector matrix
- [`data/atlas/MANIFEST.md`](../data/atlas/MANIFEST.md) — provenance of the vendored ATLAS framework data
- [`SPEC.md`](../SPEC.md) — atomic format reference
- [`PRD.md`](../PRD.md) — product requirements + milestone scope
