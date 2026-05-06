# Proposal: ATLAS Agentic Coverage Expansion

## Summary

Systematically cover all 21 agent-specific ATLAS techniques added between October 2025 and March 2026 — the techniques with zero public runnable tests anywhere. This is the core thesis of the keynote: the gap exists, here is what filling it looks like.

## Background

ATLAS added 21 agent-specific techniques in 12 months:

| Period | Techniques added |
|---|---|
| Oct 2025 | T0096, T0097, T0098, T0099, T0100, T0101 |
| Feb 2026 | T0104, T0105, T0106, T0107, T0108 |
| Mar 2026 | T0109, T0110, T0111, T0112, T0113, T0114, T0115, T0116, T0117, T0118 |

v0.1 seeds 9 of these (T0051.000, T0051.001, T0053, T0065, T0086, T0093, T0098, T0099, T0104). The remaining 12+ have no atomics in the v0.1 library.

## Coverage approach

For each technique:
1. Identify which entry vectors are applicable (not every technique applies to every vector)
2. Write one `.md` atomic per (technique, vector) cell
3. Write or reuse payload seed files
4. Verify the atomic can be executed against DVAA or a suitable synthetic target
5. Update `index.yaml` after each addition

## Priority order (post-v0.1)

Ranked by frequency in ATLAS case studies and severity of real-world impact:

1. **T0053 / direct_chat, rag_corpus** — Tool Invocation via additional vectors
2. **T0109 / mcp_server** — Agent Tool Context Poisoning (A2A context manipulation)
3. **T0110 / tool_response, mcp_server** — Agent Tool Poisoning (runtime tool manipulation)
4. **T0111 / webhook, a2a_message** — Agent Instruction Manipulation
5. **T0112 / mcp_server, a2a_message** — Agent Resource Exhaustion (DoS via tool flooding)
6. **T0096 / direct_chat** — Agent Memory Manipulation (persistent memory poisoning)
7. **T0097 / rag_corpus** — Agent Memory Exfiltration
8. **T0100 / computer_use** — Computer Use Manipulation (ClickFix-style)
9. **T0101 / email, webhook** — Agent Communication Manipulation
10. **T0086 / tool_response, webhook** — Exfiltration via additional vectors

## Success definition

Coverage is complete for this change when:
- All 21 agentic techniques have at least one atomic
- The 2D coverage matrix (technique × vector) has no empty rows in the agentic technique block
- Each atomic has been validated by `atomic-atlas validate`

## Relation to PRD

This change delivers PRD milestone **v0.2 — Chain support + broader target coverage** and partially delivers **v0.3 — Community contribution pipeline** (as new atomics come from external contributors).
