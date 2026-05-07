# Tasks: Payload Adapter

## v0.1 — implementation

### Module
- [x] `src/atomic_atlas/payload_adapter.py` — new module
  - [x] `Adaptation` dataclass with `to_markdown()` / `from_markdown()` round-trip
  - [x] `build_prompt(atomic, profile, *, recon, observed, seed_text)` returning `(system_prompt, user_prompt)`
  - [x] `_select_observed(observed, target_id, atlas_technique, include_same_technique)` filters per-target / per-technique evidence
  - [x] `adapt(atomic, profile, *, recon, observed, seed_text, model, chat_target)` async — runs LLM call, parses output
  - [x] `AdaptationParseError` exception class with raw output attached
  - [x] Lazy PyRIT import (mirrors `runner._default_red_team_chat` pattern)

### CLI
- [x] New `atomic-atlas adapt <technique>/<vector>` subcommand in `src/atomic_atlas/cli.py`
  - [x] Flags: `--profile`, `--recon`, `--observed`, `--output`, `--model`, `--include-seed/--no-seed`, `--no-llm`
  - [x] Resolves atomic via existing `_resolve_atomic` helper
  - [x] Prints bundle to stdout when no `--output`; writes to file when given
  - [x] `--no-llm` prints `system_prompt\n---\nuser_prompt\n` and exits 0
  - [x] Exit codes: 0 (success), 2 (input error), 3 (LLM failure)

### Tests (`tests/test_payload_adapter.py`)
- [x] `test_adaptation_dataclass_minimal_construction`
- [x] `test_adaptation_to_markdown_includes_required_sections`
- [x] `test_adaptation_roundtrip_through_markdown`
- [x] `test_adaptation_from_markdown_tolerates_extras`
- [x] `test_adaptation_from_markdown_raises_on_missing_payload`
- [x] `test_build_prompt_minimal_atomic_only`
- [x] `test_build_prompt_includes_recon_when_provided`
- [x] `test_build_prompt_includes_observed_evidence_truncated`
- [x] `test_select_observed_filters_same_target_different_technique`
- [x] `test_select_observed_caps_at_5_entries`
- [x] `test_adapt_async_with_mocked_chat_target`
- [x] `test_cli_adapt_writes_to_output_file`
- [x] `test_cli_adapt_no_llm_prints_prompt`

### Live verify
- [x] `atomic-atlas adapt AML.T0083/direct_chat --profile targets/dvaa_legacybot.yaml` emits a coherent bundle
- [x] Rerun with `--observed <T0084 results.json>`: rationale references harvested system-prompt content
- [x] Saved bundle can be re-loaded via `Adaptation.from_markdown` (sanity assert)

### Commit
- [x] Single commit `payload-adapter v0.1: LLM-driven init payload generation`

### Handoff to exec (follow-up commit `8081659`)
- [x] `--payload-file PATH` flag on `exec` (parses an `Adaptation` bundle, falls back to raw text, overrides `atomic.seed_prompt` in-memory before run_atomic)
- [x] `_load_payload_from_file` helper with bundle/raw/empty handling
- [x] 5 new tests: `_load_payload_from_file_bundle/raw/malformed/empty` + `test_exec_payload_file_overrides_seed_prompt`
- [x] Live verify: `adapt → exec --payload-file` end-to-end against DVAA-LegacyBot (2/2 success in 15.8s)

### Docs (commit `a696ff4`)
- [x] `docs/adapt.md` (new) — authoring guide: bundle format, observed-evidence selection rules, --no-llm dry-run, --payload-file handoff, audit trail
- [x] `docs/cli-reference.md` (new) — per-subcommand reference for every CLI flag with copy-pasteable examples
- [x] `docs/use-cases.md` (new) — three end-to-end walkthroughs (single-technique smoke, chained kill chain with `adapt`, engagement runbook)
- [x] `docs/quickstart.md` — new Step 7a covering `adapt` → `exec --payload-file` (bare and chained `--observed`)
- [x] `SPEC.md` — paragraph on `adapt` + `--payload-file` as the in-between option between hand-authored seeds and the agent runner
- [x] `PRD.md` — v0.2 milestone marked shipped with live verification numbers
- [x] `README.md` — docs index updated to link the four new doc pages

## v0.2 (deferred to a follow-on change, not in scope here)

- [ ] `--regenerate K` produces K variants for A/B testing
- [ ] Per-vector specialized system prompts (RAG-corpus poison vs MCP-tool poison vs direct-chat jailbreak)
- [ ] `atomic-atlas report --format adapted-payloads` summarizes saved bundles
- [ ] Auto-suggest `judge_examples` for the atomic when the rationale identifies a recurring True/False boundary
- [ ] Cost telemetry: log estimated $ spent per adapt call
- [ ] Optional `adapter_hints:` block in atomics for technique-specific guidance to the generator LLM (separate from `judge_guidance`, which is for the evaluator LLM)

## Lessons we want to apply

- **Promptfoo-style reproducibility.** The bundle's `generator_prompt_hash` lets operators verify two runs that look identical actually came from the same prompt. Same trick Promptfoo uses for grading consistency.
- **Audit > convenience.** A separate `adapt` step that produces a committable artifact beats an auto-magic in-`exec` generation. Operators who report to customers need the exact payload that ran.
- **One LLM call, well-structured.** Don't chain calls. The full input bundle goes in once; the output format is strictly templated. Cheaper, more deterministic, easier to test.
