# Tasks: Agent Runner

## Completed (v0.1)

- [x] CLI primitive layer: `list`, `recon`, `exec`, `report`, `validate`
- [x] `UnsupportedVectorError` typed exception for adapterless vectors; CLI catches and prints agent-runner hint
- [x] Early profile validation in `exec`: missing adapter config produces an example YAML stanza, not a downstream crash
- [x] `atomic-atlas list` command with `--vector`, `--technique`, `--json` filters
- [x] PyRIT moved to `[project.optional-dependencies] orchestrator` so the MCP server can run lightweight
- [x] Lazy PyRIT imports across all target modules; `targets/__init__.py` uses `__getattr__` for class lookup
- [x] `PyRITNotInstalledError` typed exception with install hint; `require_pyrit()` helper
- [x] `_ensure_pyrit_initialized()` helper auto-initializes SQLite memory (in-memory by default; override via `ATOMIC_ATLAS_PYRIT_DB`)
- [x] CLI `exec` checks `PYRIT_AVAILABLE` up front and exits cleanly with install hint when missing
- [x] Click command name fix: `exec_` registered as `exec`
- [x] Validate command skips `_TEMPLATE/` and `payloads/` like `load_all` does
- [x] Skill rewritten to call CLI as the primary path; manual delivery is a documented fallback

- [x] `src/atomic_atlas/mcp_server.py` — MCP server stub exposing `list_atomics`, `read_atomic`, `recon_target` (no PyRIT required); script entry point `atomic-atlas-mcp`
- [x] `[mcp-server]` optional extra in pyproject.toml so the `mcp` SDK install is opt-in

## In progress

- [ ] Document MCP server install + invocation in README

## Pending (v0.2)

- [ ] `exec_atomic` MCP tool — requires profile/auth transport design
- [ ] Hermes agent profile / system prompt
- [ ] Live integration test: MCP client connects to atomic-atlas MCP server, calls all three tools
- [ ] Decision: ship MCP server as a separate package (`atomic-atlas-mcp`) or as an entry point in this repo
- [ ] **Skill: explicit dynamic profile assembly workflow.** Update `skill/atomic-atlas.md` with a "build profile from target" loop: recon → `/info`, `/agents`, `/.well-known/*` parsing → conversational probes for domain/role inference → operator interactive prompts for credentials and scope → in-memory profile dict + target_context → `atomic-atlas exec` via subprocess. Goes beyond what the skill does informally today. Composes with the CLI's `init-profile` (skill can call it for a deterministic scaffold and then enrich).
- [ ] **MCP tool `build_profile_from_target(target_url, operator_intent)`** — agent-facing version of the same workflow, returning a profile dict the agent can pass back into `exec_atomic` (when v0.2 ships exec over MCP). Means external MCP-capable agents (Hermes etc.) get the same dynamic profile assembly without needing the Claude Code skill.
