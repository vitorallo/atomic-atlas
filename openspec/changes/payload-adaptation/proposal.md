# Proposal: Payload Adaptation

## Summary

Close the gap between atomic-atlas's design intent — payload seeds describe attack *shape*, the orchestrator adapts to each target — and what currently runs. Three concrete fixes plus an operator UX flag:

1. **`target_context` profile field** so the attacker LLM knows what target it's attacking (domain, agent role, expected tools, language, known guardrails).
2. **`RedTeamingAttack` proper integration** so atomics tagged `RedTeamingOrchestrator` actually run multi-turn adversarial mutation rather than falling back to `PromptSendingAttack`.
3. **`--hitl` flag** on `atomic-atlas exec` and `atomic-atlas runbook exec` that gates each outbound send for operator confirmation. Useful for engagement work and for debugging payload generation.
4. **`SPEC.md` documentation** of the adaptation story so atomic authors don't ship target-specific strings disguised as generic seeds.

## Problem

The DVAA harvest surfaced a real concern: a payload that lands against DVAA HelperBot may not land against a travel-agency chatbot, a healthcare assistant, or any production agent with its own domain context, role, language, and guardrails. The atomic format was designed for adaptation — `RedTeamingOrchestrator` runs an attacker LLM that's supposed to mutate the seed per target — but three gaps undercut it:

1. **The attacker LLM has no target context.** It sees the atomic's `## Attack strategy` text and generates variants blind. A jailbreak template optimized for a permissive coding agent generates the same flavor of variants when run against a guarded healthcare assistant. Detection / defense varies enormously by domain; effective attacks have to too.

2. **`RedTeamingAttack` falls back to `PromptSendingAttack`.** PyRIT 0.13 renamed orchestrators to attacks and changed the configuration shape. We migrated `PromptSendingAttack` cleanly but left `RedTeamingAttack` as a fallback (using PromptSendingAttack underneath) because the new `AttackAdversarialConfig` requires wiring we deferred. The result: every "RedTeaming" atomic is effectively static today.

3. **No operator-side preview surface.** Once `exec` runs, the operator sees the result; they don't see the payload that was sent. For debugging an unexpected pass/fail, for authorization sanity-checking on production-like targets, and for verifying that mutated payloads are sane before delivery, the operator wants a confirmation step.

## Proposed solution

Land all four threads in one OpenSpec change because they rely on the same plumbing:

- `target_context` data flows from profile → runner → attacker LLM system prompt → mutated payloads.
- `RedTeamingAttack` integration consumes `target_context` (one of its main values is making the attacker LLM target-aware).
- HITL is the operator's sanity check that `target_context` is producing reasonable output and that `RedTeamingAttack`-mutated payloads make sense.
- SPEC.md is where the adaptation story is documented so future atomic authors write seeds that benefit from the mechanism.

## Why these four together

Not separable in practice:

- `target_context` without `RedTeamingAttack` integration is just an unused profile field — `PromptSendingAttack` doesn't use an attacker LLM, so the context goes nowhere.
- `RedTeamingAttack` without `target_context` works mechanically but produces blind-attacker variants — the same gap we have today.
- HITL without either of the above is useful for debug but doesn't materially improve real-engagement outcomes.

Shipping them together is the smallest unit that produces a meaningful change.

## Scope

**v0.1 final / v0.2 cusp.** This change ships in the same window as the v0.1 catalog work; it's not a v0.2 expansion, it's a v0.1 quality completion. Without it, `RedTeamingOrchestrator`-tagged atomics are misleading (they advertise adaptation that doesn't run).

Out of scope for this change:

- `SubStringScorer` replacement (separate, tracked as a related but distinct concern about scoring rather than payload generation).
- A2ATarget (catalog work, separate).
- Lobster scaffolding (separate change).

## Status

- [ ] proposal + specs + tasks (this change)
- [ ] `target_context` profile field schema + loader
- [ ] Attacker-LLM system prompt enrichment with `target_context`
- [ ] `RedTeamingAttack` proper integration with `AttackAdversarialConfig`
- [ ] `HITLTargetWrapper` + `--hitl` flag on `exec` and `runbook exec`
- [ ] Tests for HITL wrapper, target_context loading, RedTeamingAttack path
- [ ] SPEC.md "Payload adaptation" section
- [ ] `targets/dvaa_local.yaml` updated with sample `target_context` block

## Open questions

1. **Should `target_context` be a flat dict (loose) or a typed schema (strict)?** Loose dict is more adaptable to per-target needs — a healthcare target might have a `phi_redaction_policy` field a travel target doesn't. Recommended: loose dict with a few documented well-known keys (`domain`, `agent_role`, `language`, `expected_tools`, `known_guardrails`). Atomic authors and target profile authors negotiate what other keys mean.
2. **HITL diff against last response?** When PyRIT's attacker LLM mutates across turns, showing the diff vs. the previous turn helps the operator see what changed. Recommended: yes for `--hitl --verbose`; default `--hitl` shows just the current outbound payload.
3. **Auto-confirm threshold?** For long runs (5–10 turns), prompting on every send is tedious. Recommended: `--hitl-threshold N` to auto-confirm after the operator approved N consecutive sends. Defer to v0.2 if not core to debug use.
