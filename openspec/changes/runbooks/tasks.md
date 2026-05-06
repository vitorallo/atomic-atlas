# Tasks: Runbooks

## v0.1 — completed

### Schema + parser
- [x] `schema/runbook_frontmatter.schema.json` — JSON Schema for runbook frontmatter
- [x] `src/atomic_atlas/runbook.py` — `Runbook` + `AtomicRef` dataclasses, `load(path)`, `load_all(runbooks_dir)`, frontmatter validation, atomic-ref resolution (technique+vector / atomic_path / atomic_guid), `topological_order()` with cycle + unknown-step detection. Handles `UNCLASSIFIED.<slug>` paths.
- [x] `runbooks/_TEMPLATE/runbook_template.md` — contributor template
- [x] `runbooks/README.md` — convention guide

### Executor
- [x] `src/atomic_atlas/runbook_runner.py` — `run_runbook` → `RunbookResult` + `RunbookStepResult`
- [x] Topological sort for `depends_on`
- [x] On-failure policies (stop / continue / retry); transitive skip propagation when a stop-policy parent fails
- [x] Reuses `runner.run_atomic` for each step

### CLI
- [x] `atomic-atlas runbook list [--type T] [--tactic T] [--json]`
- [x] `atomic-atlas runbook show <id>` — resolved atomic dependency graph
- [x] `atomic-atlas runbook exec <id> --target ... --profile ... --authorized`
- [x] `atomic-atlas runbook validate [<path>]`

### Catalog seed
- [x] **22 DVAA-challenge runbooks** under `runbooks/dvaa/` — full DVAA v0.8.0 catalog mapped, one runbook per challenge
- [x] Side-by-side mapping documented in `runbooks/dvaa/README.md`
- [x] Project-wide ATLAS coverage stats in `docs/atlas-coverage.md`
- [x] 13 new atomics added during the harvest (T0011.002, T0054, T0080, T0080.000, T0083, T0084, T0097, T0099/mcp_server, T0108/mcp_server, T0110, T0112, plus T0051.001/a2a_message + T0086/a2a_message + T0108/a2a_message + UNCLASSIFIED.self-replicating-memory)

### Tests
- [x] `tests/test_runbook.py` — parser, ref resolution, DAG validation (cycle + unknown-step), `UNCLASSIFIED.<slug>` resolution
- [x] `tests/test_runbook_runner.py` — chain execution with mocked atomics; `on_failure: stop / continue` policies; auth gate

## v0.2 — pending

### Reporters (deferred from v0.1)
- [ ] `runbook report --input <json> --format navigator|markdown|kill-chain`
- [ ] Navigator layer additions: kill-chain edges metadata
- [ ] New `kill-chain` report format: ATLAS-tactics-ordered narrative

### Canonical kill-chain runbooks (target-agnostic)
- [ ] `runbooks/kill-chains/indirect-pi-to-tool-exfil.md` (T0051.001 → T0053 → T0086) — keynote-demo narrative
- [ ] `runbooks/kill-chains/rag-poison-to-cred-harvest.md` (T0070 → T0082 OR T0098)
- [ ] `runbooks/kill-chains/mcp-tool-poison-to-c2.md` (T0104 → T0108)
- [ ] `runbooks/kill-chains/discover-then-exfil.md` (T0084.001 → T0086)

### Engagement-template runbooks
- [ ] `runbooks/engagement/customer-support-agent-baseline.md`
- [ ] `runbooks/engagement/mcp-deployed-agent-baseline.md`

### Docs
- [ ] Update `SPEC.md` with the runbooks section
- [ ] Update `docs/quickstart.md` with a runbook example
- [ ] Add `docs/runbooks.md` covering authoring + executor flow

### Adapter dependencies
- [ ] `A2ATarget` — unblocks live exec for `RB-DVAA-L4-02` (3 a2a_message atomics already shipped, vector adapter pending)

## v0.3 — extensions

- [ ] Real concurrency for `parallel_with`
- [ ] `target_overrides` for cross-target runbooks (compromise A, pivot to B)
- [ ] Optional `on_step` hooks for runbook-scope setup/cleanup between atomics
- [ ] Runbook-of-runbooks: a top-level runbook that references other runbooks (engagement composed of kill chains)
- [ ] Coverage badge for runbooks (% of ATLAS kill-chain stages covered)

## Decisions locked during v0.1 implementation

- Runbook GUIDs share the atomic UUID4 namespace.
- Atomic refs by `technique` + `vector` are the documented preference; `atomic_path` and `atomic_guid` are also supported.
- No `chain_into:` field on atomics — chains live in runbooks only.
- `UNCLASSIFIED.<slug>` atomics resolve as `atomics/unclassified/<slug>/<vector>.md` per `atomics/unclassified/README.md`.
