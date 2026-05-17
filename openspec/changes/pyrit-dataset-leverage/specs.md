# Specs: PyRIT Dataset Leverage

Durable policy text. This change adds **no behavior**; it records constraints
that bind future catalog/runner work.

## Policy: describe + cite, no copy

When an atomic's design is informed by an external attack corpus or template
collection (PyRIT's `jailbreak/templates`, many-shot, AdvBench, etc.):

- The atomic **describes the technique shape / variant family** in
  `## Attack strategy` and, where useful, names the source taxonomy in prose
  (e.g. "role-play-override and refusal-suppression families, cf. PyRIT
  jailbreak templates").
- The atomic **MUST NOT** embed verbatim template or corpus text as payload
  content. Payload seeds remain shape-describing per
  [`SPEC.md` → "Payload adaptation: why seeds describe shape"].
- No external corpus is vendored into the repo (`atomics/**`, `data/**`,
  `src/**`).

## In scope (future change, gated on separate approval)

- Deepening **already-covered** jailbreak/injection-family cells: `AML.T0054`,
  `AML.T0051.000`, `AML.T0051.001`, `AML.T0065` — broader `## Attack strategy`
  variant families, sharper `success_indicators` / `judge_guidance`, citing the
  PyRIT template taxonomy by name (not by copying).
- At most ~2 net-new atomics where a clean ATLAS technique mapping exists:
  many-shot / in-context poisoning; encoding/cipher evasion.

## Out of scope (permanent, unless explicitly revisited)

- Bulk-importing any corpus as atomic payloads.
- A default runtime path that seeds the runner from static external strings.
- Harm-content datasets (CBRN/drugs/etc.) — OWASP-LLM / model-safety, not
  MITRE ATLAS agentic delivery.
- Using PyRIT datasets to "cover" any of the 17 uncovered high-confidence
  agentic techniques: they are **not PyRIT-derivable** and remain
  community/authoring work under [`atlas-agentic-coverage`](../atlas-agentic-coverage/proposal.md).

## Licensing constraint

- atomic-atlas is **MIT** with a root `LICENSE`
  (`Copyright (c) 2026 Vito Rallo and atomic-atlas contributors`).
- Any future referenced material must be either (a) not redistributed (cited
  only), or (b) permissively licensed (MIT/Apache-2.0/CC-BY) **and** carried
  with its notice in a `THIRD_PARTY.md`. Research/academic/unclear-provenance
  corpora are cite-only, never vendored.
- PyRIT (MIT) as an optional pip dependency creates no notice obligation on
  this repo (not redistributed).
