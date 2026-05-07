# Tasks: Scoring Tiers

## v0.2 — implementation

### Schema + parser
- [x] Add `judge_guidance`, `judge_examples`, `scoring`, **`extractors`** to `schema/atomic_frontmatter.schema.json`
- [x] Add corresponding fields to `AtomicTest` dataclass in `parser.py`
- [x] Test parser round-trips the new fields

### Evidence dataclass (see specs.md "Evidence — first-class data type")
- [x] `src/atomic_atlas/evidence.py` — `Evidence` dataclass with `tier`, `verdict`, `matched_against`, `attack_input`, `rationale`, `matched_indicators`, `judge_reasoning`, `judge_model`, `refusal_short_circuited`, `extracted`, `duration_ms`. `to_dict()` / `from_dict()` JSON helpers.
- [x] Truncation: `matched_against` capped at 1000 chars by default; override via `ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX`
- [x] `tests/test_evidence.py` — dataclass round-trip; defaults; truncation marker

### Scorers (`src/atomic_atlas/scorers.py`)
- [x] `LLMJudgeScorer.build(...)` wrapping `pyrit.score.SelfAskTrueFalseScorer`
  - [x] Build `TrueFalseQuestion` from `success_criteria` + `judge_guidance`
  - [x] Splice `success_indicators` and `judge_examples` into `metadata`
  - [x] Default chat_target via `runner._default_red_team_chat`; override via `scoring.judge_model`
- [x] `_CheapRefusalDetector(TrueFalseScorer)` — substring match against curated refusal phrase list
- [x] `RefusalShortCircuitScorer(TrueFalseScorer)` — wrapper that runs refusal detector first, primary scorer otherwise
- [x] (Optional) re-export `pyrit.score.SelfAskRefusalScorer` for the `refusal_check: llm` mode

### Selection logic (`src/atomic_atlas/runner.py`)
- [x] `_select_scorer(atomic, profile)` factory replacing the inline if/else in `_build_attack`
- [x] `_auto_strategy(atomic)` resolves `scoring.strategy=auto` based on judge availability + atomic content
- [x] `_judge_available()` consolidates the OPENAI_API_KEY / placeholder / NO_ATTACKER_LLM check (currently duplicated in `_build_attack`)
- [x] `_build_attack` calls `_select_scorer` once and passes the result to `AttackScoringConfig`

### Composite path
- [ ] When `scoring.strategy=composite`, build child scorers from `scoring.scorers` list
- [ ] Aggregate via `pyrit.score.true_false.TrueFalseCompositeScorer` with `scoring.aggregator` (OR | AND | MAJORITY)
- [ ] Test: judge + indicators OR-composite returns true if either fires

### Evidence plumbing
- [x] `IndicatorScorer` emits `Evidence` via `score.score_metadata["evidence"]`
- [x] `LLMJudgeScorer` emits `Evidence` with `judge_reasoning` + `judge_model` populated
- [x] `RefusalShortCircuitScorer` sets `refusal_short_circuited=True` and skips primary
- [x] `runner.run_atomic` reads `score.score_metadata["evidence"]` after `attack.execute_async`, stores on `result.run_details[i]['evidence']`. Records `attack_input` (the objective) and `duration_ms`.
- [x] `runner._extract_artifacts(response_text, atomic.extractors)` runs the regex pass, merges into `evidence.extracted`
- [x] `runbook_runner` extends `RunbookStepResult` with `evidence_per_run: list[dict]`
- [x] `cli._markdown_report` renders evidence inline (matched indicators / judge reasoning / extracted bullets)
- [x] `reporters.atlas_navigator.to_navigator_layer` adds `evidence_count` and `top_extracted` per technique
- [x] Test: end-to-end evidence appears in `results.json` after a run

### Extractors backfill (v0.2 priority)
- [x] T0083 / direct_chat — `openai_api_key`, `bearer_token`, `password_field` patterns
- [x] T0098 / tool_response — credential patterns (sk-, password, secret)
- [x] T0086 / mcp_server — `/etc/passwd`-shaped (root: / daemon: lines), AWS metadata
- [x] T0084 / direct_chat — system-prompt-shape extractors (system prompt fragments)
- [ ] T0097 / direct_chat — memory-entry extraction

### Backfills
- [x] 5–10 high-value atomics get `judge_guidance` and 2–3 `judge_examples` each:
  - [x] T0051.000 / direct_chat (override compliance)
  - [ ] T0054 / direct_chat (jailbreak)
  - [x] T0083 / direct_chat (cred extraction)
  - [x] T0084 / direct_chat (config disclosure)
  - [x] T0086 / mcp_server (exfil indicator examples)
  - [x] T0098 / tool_response (cred harvest)
  - [ ] T0093 / webhook (PI via webhook)
  - [ ] T0080 / direct_chat (context poisoning)
  - [ ] T0099 / mcp_server (tool data poisoning)
- [ ] One atomic gets a `scoring: {strategy: composite, scorers: [judge, indicators], aggregator: OR}` example

### Tests
- [x] `tests/test_llm_judge_scorer.py`
  - [x] Constructs `SelfAskTrueFalseScorer` with the right `TrueFalseQuestion`
  - [x] Splices guidance + examples into metadata
  - [x] Mocks the chat_target; asserts true/false roundtrip
- [x] `tests/test_refusal_short_circuit.py`
  - [x] `_CheapRefusalDetector` matches curated phrases case-insensitively
  - [x] `RefusalShortCircuitScorer` returns false on refusal without invoking primary
  - [x] Returns primary score when no refusal detected
- [x] Update `tests/test_runner.py` (covered by new `tests/test_scorer_selection.py`)
  - [x] `_judge_available()` returns True with key set, False with placeholder, False with NO_ATTACKER_LLM
  - [x] `_select_scorer` picks judge / indicators / substring per atomic in the right order
  - [x] `_build_attack` integration: scorer selected matches the atomic's frontmatter
- [x] Live verify: `atomic-atlas exec AML.T0051.000/direct_chat ... --authorized` against DVAA HelperBot with key set → judge runs → 60–100% pass rate matching DVAA `/stats`

### Docs
- [x] `SPEC.md`: add a "Scoring tiers + evidence" section + expanded frontmatter example
- [x] `docs/quickstart.md`: add "Scoring: judge tier with first-class evidence" subsection in Step 5
- [x] `docs/scoring.md` (new): authoring guide for `judge_guidance` / `judge_examples` / `scoring:` / `extractors:`
- [x] Update PRD.md v0.2 milestone to mark scoring as shipped

## v0.3 — extensions (not in this change)

- [ ] Float-scale severity scoring (Likert)
- [ ] Multi-judge self-consistency (N=3 majority vote)
- [ ] Multi-language judge prompts driven by `target_context.language`
- [ ] Cost budget / rate-limit-aware scheduling
- [ ] Per-atomic judge model preset library (`gpt-4o-mini` for cheap, `gpt-4o` for hard)
- [ ] Remove legacy `SubStringScorer` fallback path entirely

## Lessons from Promptfoo (cited)

Inspirations and decisions, with file paths from `/Users/vito/working/promptfoo/`:

| Lesson | Source | Adopted? | Notes |
|---|---|---|---|
| LLM-judge as default | `src/redteam/plugins/base.ts` | ✅ Tier 1 of three | Wrapping PyRIT's `SelfAskTrueFalseScorer` |
| `assert-set` weighted composition | `src/types/index.ts:678+` | Partially | We adopt `scoring: {strategy: composite}` with aggregator + scorers list. No weights yet (single-objective atomics). |
| `graderGuidance` + `graderExamples` | `src/redteam/plugins/base.ts:474-502` | ✅ As `judge_guidance` + `judge_examples` |
| Refusal short-circuit | `src/redteam/plugins/base.ts:513` (`isBasicRefusal`) | ✅ As `_CheapRefusalDetector` + opt-in `SelfAskRefusalScorer` |
| Deterministic fast-path before judge | `src/redteam/plugins/dataExfil.ts:69-95` | ✅ Implicitly: refusal is the fast-path. For atomics where indicators are deterministic ground truth (e.g., `sk-` matches), `scoring: {strategy: indicators}` skips the judge. |
| JSON-mode rubrics | `src/matchers/llmGrading.ts` | ✅ via PyRIT — already enforces strict JSON output |
| Multi-judge averaging | `g-eval` | ❌ Defer to v0.3 |
| Hosted grading backend | `remoteGrading.ts` | ❌ Operator owns the LLM call |

## Decisions to lock before starting v0.2 implementation

- **Default tier when everything is available.** Recommendation: judge wins. Operator overrides per-atomic or globally.
- **Refusal detector default.** Recommendation: cheap (substring) on by default; LLM mode opt-in.
- **Judge model fallback chain.** Recommendation: `scoring.judge_model` (atomic) > `ATOMIC_ATLAS_ATTACKER_MODEL` (env) > `gpt-4o` (PyRIT default). Same as attacker LLM.
