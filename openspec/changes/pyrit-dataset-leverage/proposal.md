# Proposal: PyRIT Dataset Leverage (decision-only)

## Summary

atomic-atlas does not consume PyRIT's bundled datasets — by design, an atomic
*authors* the attack (technique × delivery-vector × success criteria) rather
than drawing from a generated/imported prompt corpus. This change answers,
durably, whether that design is leaving value on the table: **is there anything
in PyRIT's datasets we should mine to author or map new ATLAS-keyed atomics?**

Conclusion: **mostly no.** PyRIT's datasets are the wrong shape for our gap.
This change records the analysis, the **describe + cite, no copy** principle,
and the licensing posture so future catalog work does not re-litigate it or
drift toward bulk-import. **No atomics or code change in this change.**

## Background — what PyRIT 0.13 actually ships

Read-only inventory of the installed package
(`.venv/lib/python3.12/site-packages/pyrit/datasets/`):

| Asset | Path | ~Size | Nature |
|---|---|---|---|
| Jailbreak templates | `jailbreak/templates/**` | ~165 YAML | DAN/AIM/Pliny personas, prefix/style injection, cipher/encoding, refusal-suppression, model-specific |
| Many-shot corpus | `jailbreak/many_shot_examples.json` | 1001 pairs | In-context harmful Q&A (Anthropic many-shot research) |
| AdvBench seed | `seed_datasets/local/adv_bench.prompt` | ~520 | Harmful-behavior strings (MIT, llm-attacks) |
| Multi-turn executors | `executors/**` | ~10 | Crescendo / TAP / PAIR / Skeleton-Key / Context-Compliance templates |
| Harm taxonomy | `harm_definition/**` | 18 YAML | Harm categories (CBRN, drugs, etc.) |
| Converters | `prompt_converters/**` | many | Caesar/Atbash/Morse/translation/noise obfuscation |
| Remote fetchers | `seed_datasets/remote/*.py` | ~32 | HarmBench, XSTest, Aya, Forbidden-Questions, PKU-SafeRLHF, … (network) |

## Finding — off-thesis for our gap

These corpora are **generic jailbreak + harmful-content elicitation** — OWASP
LLM Top-10 / model-safety territory. atomic-atlas's gap is the **agentic ATLAS
delivery techniques**. The 17 uncovered high-confidence agentic techniques
(`data/atlas/agentic_techniques_extracted.json`, "yes" set; cross-checked
2026-05-17) are:

| ID | Name | | ID | Name |
|---|---|---|---|---|
| AML.T0002.002 | AI Agent Configuration | | AML.T0082 | RAG Credential Harvesting |
| AML.T0010.005 | AI Agent Tool (acquire) | | AML.T0084.001 | Tool Definitions (discovery) |
| AML.T0016.001 | Software Tools | | AML.T0085.000 | RAG Databases (collection) |
| AML.T0034.002 | Agentic Resource Consumption | | AML.T0085.001 | AI Agent Tools (collection) |
| AML.T0064 | Gather RAG-Indexed Targets | | AML.T0100 | AI Agent Clickbait |
| AML.T0066 | Retrieval Content Crafting | | AML.T0101 | Data Destruction via Agent Tool |
| AML.T0070 | RAG Poisoning | | AML.T0103 | Deploy AI Agent |
| AML.T0071 | False RAG Entry Injection | | AML.T0112.000 | Local AI Agent |
| AML.T0081 | Modify AI Agent Configuration | | | |

PyRIT (like Promptfoo) is chat/jailbreak-centric: **none** of these RAG / MCP /
tool / agent-config / agent-deployment techniques are addressable from a PyRIT
dataset. They remain authoring/community work — exactly the
[`atlas-agentic-coverage`](../atlas-agentic-coverage/proposal.md) lane.

## Recommended scope (narrow; for a FUTURE change, not this one)

The only on-thesis value is *depth* on the jailbreak/injection cells we already
cover. PyRIT's 165 templates are a useful **taxonomy of jailbreak shapes**. A
future change could, citing that taxonomy, broaden the `## Attack strategy`
variant-family enumeration and sharpen `success_indicators` / `judge_guidance`
of the existing exemplars — `atomics/AML.T0054/direct_chat.md` (+
`payloads/jailbreak_seed.md`), `AML.T0051.000`, `AML.T0051.001`, `AML.T0065`.
Optional/deferred: ≤2 net-new atomics with a clean ATLAS mapping (many-shot /
in-context poisoning; encoding/cipher evasion). This is explicitly **not** done
here.

## Decision

- **Describe + cite, no copy.** Atomics may describe a jailbreak/injection
  *shape family* and cite PyRIT/source; **zero** verbatim template or corpus
  text is vendored into the repo.
- No bulk corpus vendoring; no default runtime static-string import (would
  violate SPEC's "seeds describe shape, not strings").
- Harm-content datasets are explicitly **out of scope** — OWASP-LLM, not MITRE
  ATLAS.
- The 17 uncovered agentic techniques are **not** PyRIT-derivable and stay in
  the community/authoring lane.

## Licensing record — the durable "how are we doing with PyRIT" answer

- **PyRIT is MIT** (Microsoft; `License-Expression: MIT` in the installed
  dist). Consumed only as an optional pip extra (`[orchestrator]`), **not
  redistributed** — MIT's notice obligation triggers on redistribution, which
  this repo does not do. No obligation on atomic-atlas from PyRIT-the-engine.
- **Dataset risk is downstream, not PyRIT-the-engine.** HarmBench/AdvBench
  (MIT) and Aya (Apache-2.0) are permissive; Pliny/AIM/many-shot/Forbidden-
  Questions are research/academic/"source-now-compromised" provenance. The
  describe-and-cite decision keeps us clear: describing a technique *shape*
  observed in a corpus is not redistributing the corpus.
- Vendored `data/atlas/ATLAS.yaml` is under MITRE's permissive ATT&CK-style
  terms — already fine, unrelated to our code license.
- **atomic-atlas is MIT**, now with a real root `LICENSE`
  (`Copyright (c) 2026 Vito Rallo and atomic-atlas contributors`). MIT is
  one-way compatible into Apache-2.0 / a future MITRE-stewarded program — no
  relicense required if MITRE ever adopts it; inbound = outbound MIT means
  contributions are already incorporable. A `CONTRIBUTING.md` DCO
  `Signed-off-by` is the only forward-insurance for a clean *whole-project*
  relicense; **deferred**, recorded here as a conscious choice, not done.
- No `NOTICE` / `THIRD_PARTY.md` needed now (nothing third-party vendored). If
  that ever changes, add it with retained notices — deferred.

## Non-goals

No edits to `atomics/**`, no new atomics, no `src/` code, no vendored PyRIT
data, no runner seed-selection change. Implementation, if approved, is a
separate future change. The only file written outside this OpenSpec dir is the
root `LICENSE`.

## Relation to PRD

Reinforces the PRD Problem framing: PyRIT *and* Promptfoo are jailbreak-centric;
atomic-atlas's differentiator is the authored, technique-keyed catalog with a
`technique × delivery-vector` matrix — a dimension PyRIT datasets do not model.
The 17-technique gap maps to the PRD v0.2 catalog-expansion line and stays
community/authoring work, not a dataset-import task.
