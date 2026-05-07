# Tasks: Scoring Tiers

## v0.2 — implementation

### Schema + parser
- [ ] Add `judge_guidance`, `judge_examples`, `scoring` to `schema/atomic_frontmatter.schema.json`
- [ ] Add corresponding fields to `AtomicTest` dataclass in `parser.py`
- [ ] Test parser round-trips the new fields

### Scorers (`src/atomic_atlas/scorers.py`)
- [ ] `LLMJudgeScorer.build(...)` wrapping `pyrit.score.SelfAskTrueFalseScorer`
  - [ ] Build `TrueFalseQuestion` from `success_criteria` + `judge_guidance`
  - [ ] Splice `success_indicators` and `judge_examples` into `metadata`
  - [ ] Default chat_target via `runner._default_red_team_chat`; override via `scoring.judge_model`
- [ ] `_CheapRefusalDetector(TrueFalseScorer)` — substring match against curated refusal phrase list
- [ ] `RefusalShortCircuitScorer(TrueFalseScorer)` — wrapper that runs refusal detector first, primary scorer otherwise
- [ ] (Optional) re-export `pyrit.score.SelfAskRefusalScorer` for the `refusal_check: llm` mode

### Selection logic (`src/atomic_atlas/runner.py`)
- [ ] `_select_scorer(atomic, profile)` factory replacing the inline if/else in `_build_attack`
- [ ] `_auto_strategy(atomic)` resolves `scoring.strategy=auto` based on judge availability + atomic content
- [ ] `_judge_available()` consolidates the OPENAI_API_KEY / placeholder / NO_ATTACKER_LLM check (currently duplicated in `_build_attack`)
- [ ] `_build_attack` calls `_select_scorer` once and passes the result to `AttackScoringConfig`

### Composite path
- [ ] When `scoring.strategy=composite`, build child scorers from `scoring.scorers` list
- [ ] Aggregate via `pyrit.score.true_false.TrueFalseCompositeScorer` with `scoring.aggregator` (OR | AND | MAJORITY)
- [ ] Test: judge + indicators OR-composite returns true if either fires

### Backfills
- [ ] 5–10 high-value atomics get `judge_guidance` and 2–3 `judge_examples` each:
  - [ ] T0051.000 / direct_chat (override compliance)
  - [ ] T0054 / direct_chat (jailbreak)
  - [ ] T0083 / direct_chat (cred extraction)
  - [ ] T0084 / direct_chat (config disclosure)
  - [ ] T0086 / mcp_server (exfil indicator examples)
  - [ ] T0098 / tool_response (cred harvest)
  - [ ] T0093 / webhook (PI via webhook)
  - [ ] T0080 / direct_chat (context poisoning)
  - [ ] T0099 / mcp_server (tool data poisoning)
- [ ] One atomic gets a `scoring: {strategy: composite, scorers: [judge, indicators], aggregator: OR}` example

### Tests
- [ ] `tests/test_llm_judge_scorer.py`
  - [ ] Constructs `SelfAskTrueFalseScorer` with the right `TrueFalseQuestion`
  - [ ] Splices guidance + examples into metadata
  - [ ] Mocks the chat_target; asserts true/false roundtrip
- [ ] `tests/test_refusal_short_circuit.py`
  - [ ] `_CheapRefusalDetector` matches curated phrases case-insensitively
  - [ ] `RefusalShortCircuitScorer` returns false on refusal without invoking primary
  - [ ] Returns primary score when no refusal detected
- [ ] Update `tests/test_runner.py`
  - [ ] `_judge_available()` returns True with key set, False with placeholder, False with NO_ATTACKER_LLM
  - [ ] `_select_scorer` picks judge / indicators / substring per atomic in the right order
  - [ ] `_build_attack` integration: scorer selected matches the atomic's frontmatter
- [ ] Live verify: `atomic-atlas exec AML.T0051.000/direct_chat ... --authorized` against DVAA HelperBot with key set → judge runs → 60–100% pass rate matching DVAA `/stats`

### Docs
- [ ] `SPEC.md`: replace the brief "Payload adaptation" section's scoring note with a "Scoring tiers" subsection
- [ ] `docs/quickstart.md`: add a "Scoring" subsection showing the three tiers in action
- [ ] `docs/scoring.md` (new): authoring guide for `judge_guidance` / `judge_examples` / `scoring:` block
- [ ] Update PRD.md v0.2 milestone to reflect this change

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
