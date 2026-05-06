# agent-runner

Layered agent runner: Claude Code skill and MCP server, both wrapping the atomic-atlas CLI as their interface contract. The CLI is the deterministic primitive layer; the agent reasons above it and only bypasses it for vectors with no adapter.
