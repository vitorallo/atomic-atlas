---
atlas_technique: AML.T0051.001
display_name: Indirect Prompt Injection (test fixture)
interaction_vector: email
guid: 11111111-1111-4111-8111-111111111111
runs: 1
target_requires:
  - capability: email_inbound
pyrit_orchestrator: PromptSendingOrchestrator
pyrit_scorer: SubStringScorer
---

# Test fixture — adapterless vector

This is a test fixture, not a real atomic. It exists to verify that
`runner.resolve_target` raises `UnsupportedVectorError` for vectors that have
no CLI adapter (the `email` vector is reachable only via the agent runner).

Do not move this file under `atomics/` — `atomic-atlas validate` and
`atomic-atlas list` are scoped to that directory and will pick it up.

## Why this matters
Test fixture; no real-world impact.

## Success criteria
N/A.
