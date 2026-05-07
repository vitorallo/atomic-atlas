# Specs: Runbooks

## File location

```
runbooks/<category>/<slug>.md
```

`<category>` is one of `dvaa`, `kill-chains`, `engagement`. `<slug>` is kebab-case and SHOULD encode the runbook ID for findability (e.g., `L1-01__system-prompt-extraction.md`).

`runbooks/_TEMPLATE/runbook_template.md` is the contributor template (analogous to `atomics/_TEMPLATE/`). Files under `_TEMPLATE` are skipped by the loader.

## Frontmatter

| Field | Type | Required | Notes |
|---|---|---|---|
| `runbook_id` | string | ✓ | Pattern: `RB-[A-Z0-9-]+`. Stable across renames. |
| `display_name` | string | ✓ | Human-readable name. |
| `runbook_type` | enum | ✓ | One of `dvaa_challenge`, `kill_chain`, `engagement`. |
| `guid` | string | ✓ | UUID4. Same format as atomics; one ID space. |
| `target_origin` | string | — | Optional reference to source (e.g., `dvaa-L1-01`). |
| `atlas_tactics` | array | — | List of ATLAS tactic slugs traversed (`reconnaissance`, `initial_access`, `credential_access`, `discovery`, `collection`, `command_and_control`, `exfiltration`, `impact`, etc.). |
| `atomics` | array | ✓ | Ordered list of atomic refs. See below. |
| `success_criteria` | string | ✓ | Engagement-level success rule. |

### `atomics` entry shape

```yaml
atomics:
  - id: 1                              # local-to-this-runbook step id
    technique: AML.T0098               # OR atomic_path: AML.T0098/direct_chat.md
    vector: direct_chat                # OR atomic_guid: <uuid> (rename-stable)
    runs: 3                            # optional override (default: atomic.runs)
    depends_on: []                     # list of step ids that must complete first
    parallel_with: []                  # step ids that can run concurrently (v0.3)
    on_failure: stop                   # stop | continue | retry
    retry_max: 2                       # optional; only meaningful with on_failure=retry
```

Resolution order for atomic refs:
1. If `atomic_guid` is set, look up by GUID (rename-stable).
2. Else if `atomic_path` is set, load that file directly.
3. Else use `<technique>/<vector>.md` lookup against the catalog.

A runbook MUST resolve every atomic ref at parse time. Unresolvable refs are a hard error; `atomic-atlas runbook validate` catches them in CI.

## Body sections (H2)

| Section | Required | Content |
|---|---|---|
| `## Why this matters` | ✓ | Engagement-level CISO framing — why a defender should care that this *chain* succeeds. |
| `## Prerequisites` | recommended | What the operator needs (target capabilities, env vars, prerequisite runbooks). |
| `## Execution` | ✓ | Numbered prose walking the chain. References each atomic by step `id`. |
| `## Success criteria` | ✓ | Plain prose; chain-level. Often "all atomics succeed AND <integrative check>". |
| `## ATLAS kill chain` | recommended | Tactic-by-tactic narrative. e.g., "Reconnaissance: step 1 enumerates exposed tools. Credential Access: step 2 leaks SMTP_PASSWORD via tool description." |
| `## Provenance` | optional | If derived from a DVAA challenge / case study / incident, cite it here. |
| `## Cleanup` | recommended | Runbook-scope cleanup beyond what each atomic does. |

## Executor (`atomic-atlas runbook exec`)

```
atomic-atlas runbook exec <runbook_id_or_path>
  --target <url>
  --profile <yaml>
  --authorized
  [--output runbook-results.json]
  [--stop-on-failure]                  # override on_failure for entire chain
```

Algorithm:

```
1. Load runbook; resolve every atomic ref.
2. Topologically sort atomics by depends_on.
3. For each atomic in topo order:
   a. Set up the atomic (target.setup()).
   b. Run N times via existing runner.run_atomic.
   c. Record RunResult.
   d. Apply on_failure policy:
      - stop: if successes == 0, abort the runbook.
      - continue: proceed regardless.
      - retry: if successes == 0, re-run up to retry_max times, then continue.
4. Emit RunbookResult.
```

`RunbookResult` shape:

```json
{
  "runbook_id": "RB-DVAA-L1-01",
  "guid": "...",
  "atlas_tactics": ["reconnaissance", "credential_access"],
  "atomic_results": [
    {"step_id": 1, "atomic_path": "...", "successes": 3, "total_runs": 3, ...},
    {"step_id": 2, "atomic_path": "...", "successes": 1, "total_runs": 3, ...}
  ],
  "chain_success": true,
  "duration_seconds": 27.4,
  "stopped_at_step": null
}
```

`chain_success` is `true` iff every step with `on_failure=stop` had at least one success. Steps with `on_failure=continue` do not affect it.

## CLI surface

| Command | Behavior |
|---|---|
| `atomic-atlas runbook list [--type <runbook_type>] [--tactic <tactic>] [--json]` | Enumerate runbooks; filterable. |
| `atomic-atlas runbook show <id>` | Print the parsed runbook (atomics resolved, dependency graph). |
| `atomic-atlas runbook exec <id> --target ...` | Execute. Same auth gate as `exec`. |
| `atomic-atlas runbook validate [<path>]` | Validate frontmatter; resolve all atomic refs; check the dependency graph is a DAG. |
| `atomic-atlas runbook report --input runbook-results.json --format navigator\|markdown\|kill-chain` | Reports. `kill-chain` is a new format: a textual ATLAS-tactics-ordered narrative. |

## Reporter additions

- `report --format navigator` already supports atomic-level cells. Runbook reports add **kill-chain edges** to the layer JSON: a metadata field linking technique cells in chain order, rendered by Navigator as arrows when supported.
- `report --format markdown` for runbooks: per-step section + chain-level summary.
- `report --format kill-chain` (new): ATLAS-tactics-ordered narrative ("Reconnaissance succeeded (3/5). Credential Access succeeded (1/3). Exfiltration was blocked.").

## DVAA-challenge-as-runbook convention

Each DVAA challenge becomes one runbook under `runbooks/dvaa/<id>__<slug>.md`. The runbook references atomics that may live under `atomics/AML.TXXXX/` or `atomics/unclassified/`. The atomics themselves are technique-keyed and reusable; the DVAA-specific objective lives in the runbook.

This means:
- A new atomic added for a DVAA challenge is reusable in other runbooks.
- A DVAA challenge that's truly multi-step (e.g., extract system prompt → use leaked creds to register a poisoned MCP tool) is one runbook with two atomics, not one bloated atomic.
- DVAA's `prerequisites` (e.g., L1-02 depends on L1-01) become **runbook-level prerequisites**, not atomic-level — preserving the engagement narrative.

## Out of scope for this change

- Real concurrent execution (`parallel_with` enforced sequentially in v0.2).
- Cross-target runbooks (`target_overrides` per atomic — v0.3).
- LLM-driven path selection inside a runbook (defer to agent runner skill).
- Engagement timeline tracking, scoping, client metadata.
