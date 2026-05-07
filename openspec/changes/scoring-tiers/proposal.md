# Proposal: Scoring Tiers

## Summary

Replace atomic-atlas's single-scorer model with a three-tier scoring stack — **LLM judge** (preferred, when an attacker / judge LLM is available), **IndicatorScorer** (deterministic any-of-N substring matching, the fallback that #39 already shipped), **legacy SubStringScorer** (kept only for backwards compatibility, marked for v0.3 removal). Wrap PyRIT's existing `SelfAskTrueFalseScorer` and `TrueFalseCompositeScorer` rather than write our own LLM-judge plumbing. Adopt Promptfoo's `graderGuidance` / `graderExamples` per-atomic refinement plus refusal short-circuit and assert-set-style composition.

## Why now

#39 landed `success_indicators` + `IndicatorScorer` and verified end-to-end against DVAA (`5/5 success` against HelperBot). That fix made the architecture testable but doesn't address the deeper concern the user raised: **substring matching is structurally imprecise on free-text agent responses.** A response that paraphrases "I'll comply" without using any of our exact indicator strings is a real attack success that the deterministic scorer misses. An LLM judge that *reads* the response against the atomic's `## Success criteria` prose is the only architecturally honest answer.

The Promptfoo comparison (`/Users/vito/working/promptfoo/atomic-atlas-vs-promptfoo.md`) made it concrete: every red-team plugin in Promptfoo has an LLM-judge rubric by default, with deterministic fast-paths only as optimizations. atomic-atlas should converge on the same default.

PyRIT 0.13 already ships the building blocks. We don't reinvent — we wrap.

## Three tiers

```
                ┌──────────────────────────────────────────────┐
                │ Tier 1 — LLMJudgeScorer (preferred)          │
                │  pyrit.score.SelfAskTrueFalseScorer          │
                │  Question: atomic.section("Success criteria")│
                │  Hints: atomic.success_indicators            │
                │  Refusal pre-check: SelfAskRefusalScorer     │
                └──────────────────────────────────────────────┘
                                ↓ (no API key / construction fails / runtime auth failure)
                ┌──────────────────────────────────────────────┐
                │ Tier 2 — IndicatorScorer (fast deterministic)│
                │  any-of-N substring match (case-insensitive) │
                │  Already shipped via #39                     │
                └──────────────────────────────────────────────┘
                                ↓ (atomic has no success_indicators)
                ┌──────────────────────────────────────────────┐
                │ Tier 3 — SubStringScorer (legacy)            │
                │  pyrit.score.SubStringScorer                 │
                │  Logs deprecation warning; v0.3 removal      │
                └──────────────────────────────────────────────┘
```

Selection happens once in `runner._build_attack`. The chosen scorer is plugged into `AttackScoringConfig(objective_scorer=...)` and runs unchanged from there.

## Why use PyRIT's primitives, not our own

PyRIT 0.13 ships:

- `pyrit.score.SelfAskTrueFalseScorer` — LLM judge that asks a chat target a yes/no question, parses strict JSON `{score_value, description, rationale}`. Takes a `TrueFalseQuestion(true_description, false_description, category, metadata)` constructed from the atomic's prose.
- `pyrit.score.SelfAskRefusalScorer` — LLM judge for refusal detection. Used as a pre-check.
- `pyrit.score.TrueFalseCompositeScorer` — runs N child scorers via `asyncio.gather` and aggregates with `OR / AND / MAJORITY`. Lets us compose IndicatorScorer + LLMJudgeScorer if we want both signals.
- `pyrit.score.true_false.TrueFalseScoreAggregator` — the OR/AND/MAJORITY enum.

Wrapping these is ~100 lines of glue. Re-implementing the LLM-judge prompt + JSON parsing + retry + scoring would be ~500 lines plus subtle bugs we'd have to discover ourselves.

## Promptfoo-inspired refinements

Adopted from `/Users/vito/working/promptfoo/atomic-atlas-vs-promptfoo.md` §5:

1. **`judge_guidance` per atomic** (Promptfoo's `graderGuidance`). Optional frontmatter string spliced into the judge's `metadata` field. Lets the atomic author bias the judge toward the technique-specific signal.
2. **`judge_examples` per atomic** (Promptfoo's `graderExamples`). Optional list of `{response, verdict, reason}` triples spliced into metadata as concrete pass/fail examples. Improves judge accuracy materially in Promptfoo's experience.
3. **Refusal short-circuit.** Before invoking the judge on the agent's response, run `SelfAskRefusalScorer` (or a substring-based detector for cost). If the agent clearly refused, the attack failed without spending a judge call.
4. **`scoring:` frontmatter block** (Promptfoo's `assert-set`). Optional structured override of the auto-tier-selection — e.g., `scoring: {strategy: judge, threshold: 0.6}` or `scoring: {strategy: composite, scorers: [indicators, judge], aggregator: AND}`. Defaults stay automatic; the block is for atomics with non-default needs.

Specifically NOT adopting from Promptfoo:

- Multi-judge averaging / self-consistency. Defer to v0.3 if needed.
- Weighted scoring across heterogeneous metrics. atomic-atlas atomics are single-objective; weights would over-engineer.
- Hosted grading backend. Operator owns the LLM call.

## Scope

**v0.2.** Builds on #39 (already landed). The IndicatorScorer becomes the fallback rather than the primary; new code is the LLMJudgeScorer wrapper plus the selection logic plus the four refinements above.

Out of scope:

- Float-scale scorers (severity grading). v0.3.
- Multi-language judge prompts. v0.3 (target_context.language already carries the hint).
- Cost budgets / rate-limit-aware scheduling. v0.3.

## Status

- [ ] OpenSpec change shipped (this proposal + specs.md + tasks.md)
- [ ] `LLMJudgeScorer` wrapper in `src/atomic_atlas/scorers.py`
- [ ] `_select_scorer(atomic, profile)` factory in `runner.py` replaces the inline if/else in `_build_attack`
- [ ] Refusal short-circuit composed in front of the judge
- [ ] `judge_guidance`, `judge_examples`, `scoring:` block on atomic frontmatter
- [ ] Tests: judge selected when API key present; falls back to indicators on auth fail; refusal short-circuit verified; composite path; legacy SubStringScorer logs deprecation
- [ ] 5–10 atomics backfilled with `judge_guidance` / `judge_examples` to demonstrate the pattern
- [ ] SPEC.md, docs/quickstart.md updated
- [ ] Live verify against DVAA: a) judge mode (with OPENAI_API_KEY) reports honest pass/fail rates; b) auto-fallback to IndicatorScorer when key absent; c) refusal short-circuits a hardened SecureBot run

## Open questions

1. **Default tier.** When all of `success_indicators`, `## Success criteria`, and the API key are present, which tier wins? Recommendation: **judge wins by default** (matches Promptfoo's posture). Operator can force the deterministic tier with `scoring: {strategy: indicators}` per-atomic or `ATOMIC_ATLAS_SCORING=indicators` globally.
2. **Refusal scorer cost.** SelfAskRefusalScorer is itself an LLM call. Net cost: 2 calls per run when both run (refusal + judge). Promptfoo's `isBasicRefusal()` is substring-based and free. Recommendation: ship a cheap built-in `_RefusalDetector` (substring of common refusal phrases, atomic-atlas-curated) as the default short-circuit; `SelfAskRefusalScorer` opt-in via `scoring: {refusal_check: llm}`.
3. **Per-atomic judge model override.** Should `scoring:` accept a different model (e.g., gpt-4o for hard atomics, gpt-4o-mini for cheap ones)? Recommendation: yes — `scoring: {judge_model: gpt-4o-mini}`. Falls back to `ATOMIC_ATLAS_ATTACKER_MODEL`.
4. **Judge variance.** Two runs of the same atomic against the same response may produce different judge verdicts. Acceptable for v0.2 (it's well-known LLM-judge behavior). Address in v0.3 with self-consistency (N=3 majority vote) if it becomes a problem.

## Migration path

Existing atomics (27 today, 22 with `success_indicators` after #39) keep working unchanged:

- With API key: judge runs as primary, deterministic indicators stay as fallback if judge fails.
- Without API key: indicators run as primary, exactly like today.
- Without indicators: legacy `SubStringScorer` runs with a one-line deprecation warning.

The deprecation warning is the only behavior change for atomics that haven't been backfilled. v0.3 removes the legacy branch and makes `success_indicators` mandatory (or the prose criteria + judge sufficient).
