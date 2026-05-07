# Payload adapter — `atomic-atlas adapt`

`atomic-atlas adapt` uses an LLM to generate a domain-tuned **initial payload** for an atomic, given the atomic's intent + the profile's `target_context` + optional recon findings + optional prior-run evidence. Output is a markdown bundle that the operator reviews, optionally saves, and runs against the target via `atomic-atlas exec --payload-file <bundle>`.

The point: separate **payload generation** (LLM-driven, audit-able, run once) from **payload execution** (deterministic, reproducible, run N times).

## Why a separate step

Three design choices are worth understanding:

1. **Reproducibility** — `exec` stays deterministic given a saved payload. Generating-on-the-fly inside `exec` would mean every run hits the LLM and produces a slightly different payload; evidence comparisons across runs would lose meaning.
2. **Audit-ability** — Operators report the *exact payload that was sent* to customers. A markdown file the operator reviewed and committed beats a payload that lives only in PyRIT's internal state.
3. **Cost** — One generate, N runs. With auto-generation you'd pay an LLM call every run.

If you want fully automated chain orchestration ("run T0084, harvest, generate T0083 payload, run, harvest, generate T0086 payload, run") that's the agent runner / MCP server's job. `adapt` is the explicit, controllable, audit-friendly alternative.

## TL;DR

```bash
# 1. Generate the bundle
atomic-atlas adapt AML.T0083/direct_chat \
  --profile targets/dvaa_legacybot.yaml \
  --output atomics/AML.T0083/payloads/legacybot.md

# 2. (Review the bundle in your editor)
$EDITOR atomics/AML.T0083/payloads/legacybot.md

# 3. Run it
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --payload-file atomics/AML.T0083/payloads/legacybot.md \
  --runs 3 --authorized
```

## Bundle format

`adapt` emits a canonical markdown document that round-trips losslessly through `Adaptation.from_markdown` / `to_markdown`. Layout:

```markdown
---
atlas_technique: AML.T0083
interaction_vector: direct_chat
target_id: dvaa_legacybot
generator_model: gpt-4o
generator_prompt_hash: "sha256:5d823883…"
generated_at: "2026-05-07T11:36:32Z"
---

# Adapted payload for AML.T0083/direct_chat against dvaa_legacybot

## Rationale
<2-4 sentences on framing choices, citing target_context fields and any
 observed evidence the LLM was given.>

## Payload
> The literal payload to send. Multi-line blockquote — preserved
> verbatim as the seed_prompt when piped into `exec --payload-file`.

## Suggested observations
- What the operator should look for in the response.

## Suggested indicators
- Substrings that, if present, confirm success.
```

The frontmatter includes a `generator_prompt_hash` so two operators can verify they generated from identical inputs (atomic + profile + observed). The hash covers `system_prompt + user_prompt`.

## Inputs

All optional except `--profile`:

| Input | Purpose |
|---|---|
| Atomic body sections (`## Why this matters`, `## Attack strategy`, `## Success criteria`, `## Interaction`) | Defines the technique-level intent the payload must satisfy. |
| Atomic frontmatter (`success_indicators`, `judge_guidance`, `judge_examples`) | Carries scoring hints to the generator so the payload aligns with what the judge tier checks for. |
| Profile `target_context` (`domain`, `agent_role`, `language`, `expected_tools`, `known_guardrails`) | The target's identity the LLM tunes the payload against. |
| `--recon` JSON (output of `atomic-atlas recon`) | Discovered endpoints, applicable techniques, target capability hints. |
| `--observed` JSON (prior `results.json`) | Per-run `evidence` from earlier exec runs against the same target. The adapter uses `judge_reasoning`, `matched_indicators`, and especially `extracted` artifacts (e.g., harvested system-prompt fragments). |
| Existing seed (`atomics/<technique>/payloads/*.md`) | Shape reference the LLM adapts. Disable with `--no-seed`. |

## Selecting observed evidence

When `--observed` points at a multi-atomic results.json, the adapter doesn't dump everything into the prompt. Selection rules (in order):

1. Filter to entries whose target matches the current profile (by `target_context.target_id` or profile filename stem).
2. **Drop same-technique entries by default** — the adapter wants prior *reconnaissance* context (T0084 system-prompt leak feeding a T0083 cred extraction), not the same atomic's prior runs. Override with `--include-same-technique` for "I ran this and it almost worked" iterations.
3. Prefer `verdict=True` entries (the agent leaked something).
4. Within those, prefer non-empty `extracted` (concrete artifacts).
5. Within those, prefer `tier="judge"` over `tier="indicators"` (richer reasoning).
6. Cap at 5 entries; truncate `judge_reasoning` to 400 chars per entry.

This keeps the prompt under control regardless of how many prior runs you feed it.

## Dry-run with `--no-llm`

Print the prompt that would be sent without calling the LLM:

```bash
atomic-atlas adapt AML.T0083/direct_chat --profile targets/dvaa_legacybot.yaml --no-llm
```

Useful for:
- Reviewing what context the LLM actually sees before committing to a generate.
- Comparing prompts when you change `target_context` or add `--observed`.
- Running offline / in CI to sanity-check the prompt builder.

## Configuration

Environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `OPENAI_API_KEY` | Required for the LLM call. | — |
| `OPENAI_API_BASE` | Override the OpenAI endpoint (LiteLLM proxy, vLLM, etc.). | `https://api.openai.com/v1` |
| `ATOMIC_ATLAS_ADAPTER_MODEL` | Generator model. | `gpt-4o` |
| `ATOMIC_ATLAS_ATTACKER_MODEL` | Fallback for the generator model. | `gpt-4o` |

Pin all of these in repo-root `.env` (auto-loaded; `.env` wins over the shell). No CLI flags for model selection — keeping the CLI surface tight. See [`docs/install.md`](install.md#llm-providers--openai-openrouter-ollama-local-llms) for OpenRouter / Ollama / vLLM setup.

## Handing off to `exec`

Two ways to run an adapted bundle:

### Direct (recommended)

```bash
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --payload-file atomics/AML.T0083/payloads/legacybot.md \
  --runs 3 --authorized
```

`--payload-file` parses the bundle, extracts the `## Payload` blockquote, and overrides the atomic's `seed_prompt` in-memory before run. The flag also accepts plain text files (used verbatim) — useful when you have a hand-crafted payload that isn't an `adapt` bundle.

### Commit it as the atomic's payload

```bash
# Saved payload becomes the atomic's default seed
mv adapted.md atomics/AML.T0083/payloads/legacybot.md
# Edit atomics/AML.T0083/direct_chat.md frontmatter to reference it:
#    seed_prompt: |
#      <copy the ## Payload blockquote content here>
git add atomics/AML.T0083/
```

## What the LLM is told NOT to do

The system prompt explicitly disallows:

- Multiple variants per response (the operator runs ONE payload).
- Mutation strategies / "alternative framings" lists.
- Refusals — authorization is asserted by the caller.
- Commentary, preamble, or epilogue outside the four required sections.

Output is templated tightly so the parser can extract the payload deterministically.

## Limits + gotchas

- **DVAA is a phrase-matcher, not a real LLM.** A semantically-correct LLM-generated payload may not hit DVAA's narrow trigger set on the first turn. Use `RedTeamingOrchestrator` orchestration to let the attacker LLM mutate the seed across turns, or use `adapt` against real LLM targets.
- **Variance is intentional.** Two `adapt` calls with identical inputs may produce different bundles. The `generator_prompt_hash` lets you verify the *inputs* were identical; the LLM's stochasticity is by design.
- **No automatic atomic backfill.** The adapter does not write back to the atomic's frontmatter (e.g., to add `judge_examples`). Generated artifacts live alongside the atomic, not inside it.
- **No regeneration loop.** If a payload fails, run `adapt` again with `--observed` updated (now containing the failure evidence). The adapter doesn't auto-retry.
- **Generator ≠ judge.** `--model` here is the *generator* model. `scoring.judge_model` in the atomic's frontmatter is the *evaluator* model. Different concerns, different flags.
