# payload-adaptation

Close the gap between atomic-atlas's design intent (payload seeds describe shape; the orchestrator adapts to each target) and what currently runs (attacker LLM is blind, RedTeamingAttack falls back to PromptSendingAttack, no operator-side preview surface). Adds `target_context` to target profiles, completes the RedTeamingAttack integration, and ships a `--hitl` flag that gates each outbound send for operator confirmation.
