# vulnerable-agent

**Lobster** — a LangGraph agent at `examples/lobster/` that is intentionally vulnerable to as many MITRE ATLAS agentic techniques as possible. Each weakness is coded explicitly, tagged with its `AML.TXXXX` ID at the vuln site, and exercised by a corresponding atomic-atlas atomic. The reference implementation of the ATLAS agentic technique surface, runnable in one `docker compose up`. One claw per technique.
