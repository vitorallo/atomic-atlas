# Proposal: Vulnerable Agent (Lobster)

## Summary

Ship **Lobster** — a LangGraph agent at `examples/lobster/` that is intentionally vulnerable to as many MITRE ATLAS agentic techniques as we can fit in a small reference implementation. The name fits the project's "claw" framing: one coded vulnerability per technique, each one a claw the agent can be grabbed by. Each weakness is coded explicitly, tagged with its `AML.TXXXX` ID in the source (`# ATLAS: AML.T0086 — Exfiltration via Agent Tool`), and exercised by a corresponding atomic-atlas atomic. The agent becomes the **physical reference implementation** of the ATLAS agentic technique surface — a place a practitioner can point at and say "this is what AML.T0086 looks like in 8 lines of LangGraph."

The runtime stack is plain-vanilla — LangGraph + ChromaDB + FastAPI shim — so the realism story still lands ("this is what production agents are built on"). The vulnerabilities sit on top of that vanilla foundation as named, tagged, hardenable behaviors.

## Problem

Today the demo target is **DVAA** — third-party, broad surface, but bespoke. It works, but:

1. **Setup friction.** Two repos for a new contributor or keynote demo.
2. **Coupling risk.** Single-org backed; upstream breaks → demo breaks.
3. **No ATLAS mapping.** DVAA has its own taxonomy; there's no obvious "this is where AML.T0099 lives."
4. **Doesn't tell the right story.** atomic-atlas is ATLAS-keyed; its canonical demo target should be too.

## Proposed solution: ATLAS-keyed vulnerability reference

A LangGraph-based agent where each ATLAS technique that's testable on a single agent has a corresponding **coded** vulnerability:

```python
# src/tools.py

@tool
def external_lookup(url: str) -> str:
    """Fetch a URL and return the body. Used by the agent for research."""
    # ATLAS: AML.T0086 (Exfiltration via Agent Tool) — no URL allowlist.
    # ATLAS: AML.T0099 (Tool Data Poisoning) — return value trusted by the
    # LLM with no provenance marker.
    return httpx.get(url, timeout=10).text
```

The intent is that a reader can:
- Read the agent source and see exactly which ATLAS techniques it's vulnerable to.
- Run `atomic-atlas exec` against it and watch each technique succeed.
- Patch a specific `# ATLAS: AML.TXXXX` site and watch the corresponding atomic stop succeeding (regression test for mitigations).

This is what makes it a reference implementation instead of "just another vulnerable demo."

## Coverage target

The atlas-agentic-coverage change tracks 21 agentic ATLAS techniques as the v0.1+v0.2 catalog target. The vulnerable agent aims to cover **17 of those 21** in v0.2 — every technique that's testable on a single-process agent without computer-use sandboxing or full A2A protocol implementation:

- ✓ Covered in v0.2 (real ATLAS v5.6.0 IDs): T0051.000, T0051.001, T0053, T0065, T0070, T0080, T0080.000, T0083, T0084.001, T0086, T0093, T0096, T0097, T0098, T0099, T0101, T0104, T0108, T0109, T0110, T0111, T0112
- ✓ Covered in v0.2 (unclassified — no current ATLAS technique covers the pattern): UNCLASSIFIED.scope-violation, UNCLASSIFIED.authorization-bypass
- ✗ Deferred to v0.3: T0100 (Computer Use — needs sandbox), T0102 (Memory Persistence — needs cross-restart store), AML.T0086/a2a_message (was phantom T0115; now a matrix cell of T0086), UNCLASSIFIED.chain-hijack-a2a (was phantom T0116)

The full mapping table lives in [specs.md](specs.md).

## Why LangGraph

- Most-recognized modern agentic SDK in practitioner deployments.
- Native primitives for every vector we test: `ChatModel` (direct_chat), `Chroma` vectorstore (rag_corpus), `@tool` decorator (tool_response), `langchain-mcp-adapters` (mcp_server).
- The "default-configured agent is vulnerable" story is honest because the SDK doesn't force hardening.

The SDK is a v0.2 commitment, not a forever lock-in. v0.3 can add sibling examples for OpenAI Agents SDK / Anthropic SDK to demonstrate framework-portability of atomic-atlas.

## Why ship our own vs. relying on DVAA

| | DVAA | examples/vulnerable_agent (this proposal) |
|---|---|---|
| Setup | clone separate repo + follow upstream README | `cd examples/vulnerable_agent && docker compose up` |
| Stack | bespoke FastAPI | LangGraph — what practitioners actually use |
| ATLAS mapping | implicit, project-specific taxonomy | explicit `# ATLAS: AML.TXXXX` tag at every vuln site |
| Coupling | atomic-atlas atomics break if DVAA breaks | atomic-atlas owns both ends; CI catches drift |
| Vector growth | wait for upstream | we add a vuln + atomic in one PR |

DVAA stays referenced as the elaborate alternative. Our LangGraph agent is the **default**.

## Non-goals

- **Not a hardened agent.** That's the point.
- **Not feature-rich.** Single LLM, three base tools + dynamic tool registration, one vector store, simple memory. Just enough to host the ATLAS technique surface.
- **No A2A or computer-use in v0.2.** Deferred to v0.3 along with the four ATLAS techniques that require those scaffoldings.

## Scope

**v0.2** (post-keynote). The keynote demo (v0.1) continues to target DVAA — no rush, no risk of half-finished code on stage. This change captures planning + scaffolding now so implementation lands immediately after the keynote ships.

## Status

- [ ] proposal + specs + tasks (this change)
- [ ] LangGraph agent skeleton + Dockerfile + docker-compose.yml
- [ ] 22 weaknesses tagged in the agent source: 20 ATLAS-v5.6.0 IDs + 2 UNCLASSIFIED.* slugs (full table in specs.md)
- [ ] Each tagged vulnerability has a corresponding atomic in `atomics/` (some new for v0.2)
- [ ] CI: spin up the agent, run all atomics against it, verify reasonable success rate per technique
- [ ] README documenting safety boundary, ATLAS mapping table, and how to add a new vulnerability + atomic together

## Open questions

1. **LLM backing.** `ChatOpenAI` default + documented `ChatAnthropic` swap (recommended), vs. abstract behind a config knob from day one.
2. **MCP client.** `langchain-mcp-adapters` directly (recommended), vs. thin custom wrapper for clarity.
3. **Mitigations toggle.** Ship the agent with a `VULNAGENT_HARDEN=AML.T0086,AML.T0099` env that turns specific vulnerabilities off — useful for testing detection / mitigation atomics in v0.3. Recommended yes, but as a v0.3 task; v0.2 ships fully unhardened.
