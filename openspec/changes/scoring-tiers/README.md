# scoring-tiers

Three-tier scorer architecture for atomic-atlas: LLM judge primary, IndicatorScorer deterministic fallback, legacy SubStringScorer marked for deprecation. Wraps PyRIT's `SelfAskTrueFalseScorer` + `TrueFalseCompositeScorer` rather than reinventing. Adds Promptfoo-inspired refinements (graderGuidance / graderExamples, refusal short-circuit, assert-set-style composition). Closes the gap that #39 (`IndicatorScorer`) opened: deterministic substring matching is a fallback, not the primary path.
