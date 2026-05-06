# Tasks: Payload Adaptation

## Implementation

### `target_context` profile field
- [ ] Document well-known keys in this change's specs.md
- [ ] `runner.load_profile` carries `target_context` through (no schema validation; loose dict)
- [ ] `targets/dvaa_local.yaml` gets a sample `target_context` block as documentation
- [ ] Test: profile with `target_context` loads cleanly; absent key defaults to `{}`

### Attacker LLM enrichment
- [ ] `runner._default_red_team_chat()` accepts an optional `target_context` arg
- [ ] When non-empty, prepends a context block to the attacker LLM's effective instructions

### `RedTeamingAttack` integration
- [ ] `runner._build_attack` constructs `AttackAdversarialConfig` for `RedTeamingOrchestrator`-tagged atomics using the target_context-enriched attacker LLM
- [ ] Returns actual `RedTeamingAttack` rather than `PromptSendingAttack` fallback
- [ ] Test: a `RedTeamingOrchestrator`-tagged atomic resolves to `RedTeamingAttack` instance

### HITL
- [ ] `src/atomic_atlas/hitl.py` — `HITLTargetWrapper` + `HITLAbortError`
- [ ] `runner.run_atomic` accepts `hitl: bool = False`; wraps target if True
- [ ] `runbook_runner.run_runbook` accepts `hitl: bool = False`; passes through to per-step `run_atomic`
- [ ] CLI: `--hitl` flag on `atomic-atlas exec` and `atomic-atlas runbook exec`
- [ ] Abort propagation: `HITLAbortError` short-circuits remaining runs / steps cleanly; cleanup still runs
- [ ] Tests:
  - [ ] Wrapper forwards on `y`
  - [ ] Wrapper returns synthetic error on `n`
  - [ ] Wrapper raises `HITLAbortError` on `a`
  - [ ] Runner catches abort and returns partial RunResult
  - [ ] Runbook runner catches abort and marks subsequent steps skipped

### Documentation
- [ ] `SPEC.md` — add "Payload adaptation: why seeds describe shape" under "Design principles"
- [ ] `docs/install.md` — note that target_context is optional but recommended for non-DVAA / non-Lobster targets
- [ ] `docs/targets.md` — add a `target_context` example
- [ ] Update `docs/quickstart.md` with a brief HITL example
- [ ] Update `runbooks/dvaa/README.md` if any DVAA runbooks should suggest using `--hitl`

## Verification

- [ ] `pytest tests/ -q` — all existing tests pass; new HITL tests pass
- [ ] Live: `atomic-atlas exec AML.T0051.000/direct_chat --target http://localhost:7002/v1 --profile targets/dvaa_local.yaml --authorized --hitl` — interactive prompt before each send; `y` / `n` / `a` all behave correctly
- [ ] Live: `atomic-atlas runbook exec RB-DVAA-L1-02 --target http://localhost:7003/v1 --profile /tmp/legacybot.yaml --authorized --hitl` — interactive prompt for each step's runs; abort propagates through the chain
- [ ] Live: profile with `target_context` produces visibly different RedTeamingAttack variants vs. profile without (visible via `--hitl`)
- [ ] `atomic-atlas validate` — 27 atomics still valid
- [ ] `atomic-atlas runbook validate` — 22 runbooks still valid

## Out of scope

- `SubStringScorer` replacement (#39 — separate)
- `A2ATarget` (catalog work, separate)
- Auto-confirm threshold for HITL (defer)
- LLM judge scorer (separate)
