# `runbooks/` — atomic chains for engagement-level objectives

A **runbook** is an ordered chain of atomics that together accomplish an engagement-level objective: a DVAA challenge solve, a real-world kill chain (recon → initial-access → cred-access → exfil), or a custom assessment script.

The atomic catalog under `atomics/` stays **technique-keyed** and reusable. Runbooks compose those atomics into multi-step assessments. A single atomic might appear in many runbooks; a single runbook references many atomics.

## Why runbooks exist

- Real attacks are chains, not single atomics. ATLAS techniques are tactic-keyed; a kill chain is a path through tactics.
- DVAA challenges and similar CTF-style targets pose multi-step objectives that decompose into 2-5 atomics.
- Practitioners think in engagements, not isolated tests. They write runbooks and run atomics inside them.
- The keynote-demo narrative ("T0051.001 → T0053 → T0086") is naturally a runbook.

## Layout

```
runbooks/
├── README.md                         (this file)
├── _TEMPLATE/
│   └── runbook_template.md           (contributor template — skipped by loader)
├── dvaa/                             (one runbook per DVAA challenge)
│   ├── L1-01__system-prompt-extraction.md
│   ├── L1-02__api-key-leak.md
│   └── ...
├── kill-chains/                      (canonical ATLAS kill-chain runbooks)
│   ├── indirect-pi-to-tool-exfil.md  (T0051.001 → T0053 → T0086)
│   └── ...
└── engagement/                       (template runbooks for engagements)
    ├── customer-support-agent-baseline.md
    └── mcp-deployed-agent-baseline.md
```

## File format

One markdown file per runbook. YAML frontmatter for machine-readable metadata; markdown body for human-readable narrative. Schema lives at `schema/runbook_frontmatter.schema.json`.

Frontmatter fields:

| Field | Required | Notes |
|---|---|---|
| `runbook_id` | ✓ | Pattern: `RB-[A-Z0-9-]+`. Stable across renames. |
| `display_name` | ✓ | Human-readable name. |
| `runbook_type` | ✓ | `dvaa_challenge` \| `kill_chain` \| `engagement` |
| `guid` | ✓ | UUID4. Same format as atomics; one ID space. |
| `target_origin` | — | Optional. e.g., `dvaa-L1-01`. |
| `atlas_tactics` | — | List of ATLAS tactic slugs traversed. |
| `atomics` | ✓ | Ordered list of atomic refs (see below). |
| `success_criteria` | ✓ | Engagement-level success rule. |

`atomics` entries reference atomics by `<technique>/<vector>` path (preferred for human-written runbooks) or by `atomic_guid` (rename-stable). Each entry has a step `id`, optional `depends_on`, and an `on_failure` policy (`stop` \| `continue` \| `retry`).

Body sections (H2):
- `## Why this matters` — engagement-level CISO framing
- `## Prerequisites` — operator inputs, prerequisite runbooks
- `## Execution` — numbered prose walking the chain
- `## Success criteria` — chain-level
- `## ATLAS kill chain` — tactic-by-tactic narrative
- `## Provenance` — citation if derived from a DVAA challenge / case study / incident
- `## Cleanup` — runbook-scope cleanup beyond what each atomic does

See `_TEMPLATE/runbook_template.md` for a working example.

## How to author a runbook

1. Pick a category (`dvaa`, `kill-chains`, `engagement`).
2. Copy `_TEMPLATE/runbook_template.md` to your category dir; rename to `<id-slug>.md`.
3. Fill the frontmatter; reference existing atomics by `<technique>/<vector>` path.
4. If a referenced atomic doesn't exist yet, write the atomic first under `atomics/`.
5. Run `atomic-atlas runbook validate <path>` to confirm the frontmatter parses and every atomic ref resolves.
6. Open a PR — one runbook per PR (same as atomics).

## Running a runbook

```bash
atomic-atlas runbook list                                    # browse the catalog
atomic-atlas runbook show RB-DVAA-L1-01                      # view parsed runbook
atomic-atlas runbook exec RB-DVAA-L1-01 \
  --target http://target.local \
  --profile targets/dvaa_local.yaml \
  --authorized
atomic-atlas runbook report --input runbook-results.json --format kill-chain
```

The executor walks the dependency DAG, runs each atomic via the existing `runner.run_atomic`, and emits a chain-level result.

## DVAA challenges as runbooks

Each of DVAA's 22 published challenges (visible at `http://localhost:9000/api/challenges` when DVAA is running) maps to one runbook under `runbooks/dvaa/`. The challenge's `prerequisites` field becomes the runbook's prerequisite chain; the `objectives` become the chain-level success criteria; the underlying ATLAS techniques become the referenced atomics.

The atomics themselves are technique-keyed — they're useful in any runbook, not just the DVAA one that prompted writing them.
