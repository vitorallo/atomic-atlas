# CLI reference

Every `atomic-atlas` subcommand, every flag, copy-pasteable examples. Skim the synopsis, jump to the flag table, copy an example.

```text
atomic-atlas <subcommand> [OPTIONS] [ARGS]
```

| Subcommand | Purpose |
|---|---|
| [`recon`](#recon) | Probe a target, fingerprint guardrails, suggest applicable atomics. |
| [`list`](#list) | Browse the atomic catalog. |
| [`validate`](#validate) | Schema-check atomic frontmatter. |
| [`adapt`](#adapt) | LLM-generate a target-tuned initial payload. |
| [`exec`](#exec) | Run an atomic against a target. |
| [`report`](#report) | Render results — Navigator JSON, coverage matrix, markdown. |
| [`runbook list`](#runbook-list) | Browse the runbook catalog (chains of atomics). |
| [`runbook exec`](#runbook-exec) | Run a runbook (kill chain / engagement) end-to-end. |

The base install supports `list`, `recon`, `report`, `validate`. `exec`, `adapt`, and `runbook exec` need PyRIT and (for `adapt` + LLM judge tier) an OpenAI-compatible LLM:

```bash
pip install 'atomic-atlas[orchestrator]'   # adds PyRIT + the LLM-driven paths
```

---

## `recon`

Enumerate entry vectors and fingerprint guardrails for a target.

```bash
atomic-atlas recon --target <BASE_URL> [--auth-header <VALUE>]
```

| Flag | Purpose |
|---|---|
| `--target TEXT` | **Required.** Target agent base URL. |
| `--auth-header TEXT` | Authorization header (Bearer token or API key). |

Output is a human summary table; pipe through `tee recon.json` if you want to feed it into `adapt --recon`. (See [`docs/use-cases.md`](use-cases.md) for the chain.)

**Example:**

```bash
atomic-atlas recon --target http://localhost:7003/v1
# Output: discovered endpoints, applicable techniques, vector evidence
```

---

## `list`

Browse atomics — what's covered, by vector or technique.

```bash
atomic-atlas list [--vector <V>] [--technique <T>] [--json]
```

| Flag | Purpose |
|---|---|
| `--vector TEXT` | Filter by `interaction_vector` (e.g. `direct_chat`, `mcp_server`). |
| `--technique TEXT` | Filter by ATLAS technique ID (e.g. `AML.T0051.001`). |
| `--json` | Emit JSON instead of a human table. |

**Examples:**

```bash
atomic-atlas list                                     # full catalog
atomic-atlas list --vector direct_chat                # all direct-chat atomics
atomic-atlas list --technique AML.T0083 --json | jq   # programmatic
```

---

## `validate`

Schema-check atomic frontmatter. Validates all atomics if no path given.

```bash
atomic-atlas validate [ATOMIC_PATH]
```

**Examples:**

```bash
atomic-atlas validate                                 # all atomics
atomic-atlas validate AML.T0083/direct_chat           # single atomic
atomic-atlas validate atomics/AML.T0083/direct_chat.md
```

Exit code 0 = valid; non-zero = at least one validation error.

---

## `adapt`

Generate an LLM-tuned initial payload for an atomic against a specific target. Produces a markdown bundle (rationale + payload + suggested observations + suggested indicators). Full guide: [`docs/adapt.md`](adapt.md).

```bash
atomic-atlas adapt <TECHNIQUE/VECTOR> --profile <P> [...]
```

| Flag | Purpose |
|---|---|
| `--profile PATH` | **Required.** Target profile YAML. |
| `--recon PATH` | Optional `atomic-atlas recon` JSON output. |
| `--observed PATH` | Optional `results.json` with prior-run evidence to feed in. |
| `--output PATH` | Write the bundle to a file (default: stdout). |
| `--target-id TEXT` | Identifier in the bundle's `target_id` field (default: profile filename stem). |
| `--include-seed / --no-seed` | Include the existing payload seed as a shape reference (default: include). |
| `--include-same-technique` | Include same-technique entries when feeding observed evidence (default: skip them). |
| `--no-llm` | Print the would-be prompt and exit (no LLM call). |

**Examples:**

```bash
# Bare adapt — atomic intent + profile target_context only.
atomic-atlas adapt AML.T0083/direct_chat \
  --profile targets/dvaa_legacybot.yaml \
  --output adapted.md

# With recon + prior evidence (the kill-chain pattern).
atomic-atlas adapt AML.T0083/direct_chat \
  --profile targets/dvaa_legacybot.yaml \
  --recon recon.json \
  --observed results-from-T0084.json \
  --output adapted.md

# For a cheaper model, set ATOMIC_ATLAS_LLM_MODEL=gpt-4o-mini in .env
# (or any model your OPENAI_API_BASE provider supports — see docs/install.md).

# Dry-run: print the prompt, don't call the LLM.
atomic-atlas adapt AML.T0083/direct_chat \
  --profile targets/dvaa_legacybot.yaml --no-llm
```

---

## `exec`

Run an atomic test against a target.

```bash
atomic-atlas exec <ATOMIC_PATH> --target <URL> [--profile <P>] [...]
```

| Flag | Purpose |
|---|---|
| `--target TEXT` | **Required.** Target agent base URL. |
| `--profile PATH` | Target profile YAML (adapters per vector + `target_context`). |
| `--runs INTEGER` | Override the atomic's `runs` field. |
| `--output TEXT` | Legacy: append to a single results JSON file. Prefer `--engagement`, which auto-accumulates to `atomic-atlas-engagement/results.jsonl` in your cwd. |
| `--engagement PATH` | Engagement directory for accumulating results. Default: `ATOMIC_ATLAS_ENGAGEMENT_DIR` env, else `./atomic-atlas-engagement/`. Auto-created. |
| `--authorized` | **Required flag.** Confirms you have authorization to test the target. |
| `--hitl` | Human-in-the-loop: confirm each outbound message before send. |
| `--payload-file PATH` | Override the atomic's `seed_prompt` with the payload from this file. Accepts `atomic-atlas adapt` bundles (parsed) or plain text (used verbatim). |

**Examples:**

```bash
# Default: scoring auto-selects judge tier when OPENAI_API_KEY is set.
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized

# With an adapt bundle (the clean handoff from `adapt`).
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --payload-file adapted.md \
  --runs 3 --authorized

# HITL — review every outbound message.
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized --hitl

# Force deterministic / no-LLM scoring (offline or untrusted-target runs).
ATOMIC_ATLAS_OFFLINE=1 \
atomic-atlas exec AML.T0083/direct_chat \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --runs 3 --authorized
```

Useful environment variables:

| Variable | Effect |
|---|---|
| `OPENAI_API_KEY` | API key for the LLM provider. Required for OpenAI; optional for Ollama / local LLMs that don't validate it. |
| `OPENAI_API_BASE` | LLM endpoint. Default `https://api.openai.com/v1`. Set to `https://openrouter.ai/api/v1`, `http://localhost:11434/v1` (Ollama), or any OpenAI-compatible URL. |
| `ATOMIC_ATLAS_LLM_MODEL` | LLM model name used by the judge, attacker, and adapter (default `gpt-4o`). Whatever your `OPENAI_API_BASE` provider supports. |
| `ATOMIC_ATLAS_OFFLINE=1` | Disable every LLM call site (judge tier, attacker LLM, adapter). Forces deterministic indicator scoring + `PromptSendingAttack`. |

See [docs/install.md](install.md#llm-providers--openai-openrouter-ollama-local-llms) for provider-by-provider setup (OpenRouter free models, Ollama, vLLM, LiteLLM).

A few additional vars exist for tests / development (`ATOMIC_ATLAS_ATOMICS_DIR`, `ATOMIC_ATLAS_SKIP_DOTENV`, `ATOMIC_ATLAS_PYRIT_DB`, `ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX`); they're stable but not part of the operator surface.

See [`docs/scoring.md`](scoring.md) for the scorer-tier details.

---

## `report`

Render accumulated atomic-atlas results — Navigator layer, coverage matrix, evidence-rich markdown, or stakeholder-facing **engagement findings**.

```bash
atomic-atlas report [--engagement DIR | --input FILE] --format <FMT> [--output FILE] [--target ID] [--since TS]
```

| Flag | Purpose |
|---|---|
| `--engagement PATH` | Engagement directory to read from. Default: `ATOMIC_ATLAS_ENGAGEMENT_DIR` env, else `./atomic-atlas-engagement/`. Reads `results.jsonl` accumulated across `exec` runs. |
| `--input PATH` | Legacy: a single `results.json` from one `exec` invocation. Mutually exclusive with `--engagement`. |
| `--format navigator\|coverage\|markdown\|findings` | Output format. Default: `navigator`. The `findings` format requires the engagement source (it aggregates across runs). |
| `--output TEXT` | Write to file (default: stdout). |
| `--target TEXT` | Filter to one `target_id` (engagement source only). |
| `--since TEXT` | ISO-8601 timestamp prefix; only entries recorded after this. (engagement source only). |

**Examples:**

```bash
# Stakeholder-facing engagement report — verdict + severity per (atomic, target).
atomic-atlas report --format findings --output engagement-report.md

# Same, but only one target's results
atomic-atlas report --format findings --target dvaa_legacybot

# Only this week's runs
atomic-atlas report --format findings --since 2026-05-05

# ATLAS Navigator JSON layer (open at https://mitre-atlas.github.io/atlas-navigator/)
atomic-atlas report --format navigator --output dvaa.layer.json

# Compact coverage matrix in the terminal.
atomic-atlas report --format coverage

# Markdown report with per-run evidence inline.
atomic-atlas report --format markdown --output detailed.md

# Legacy single-file mode still works
atomic-atlas report --input legacy-results.json --format markdown
```

### About the engagement directory

Every `exec` and `runbook exec` invocation appends a timestamped entry to:

```
atomic-atlas-engagement/
    results.jsonl           # one JSON object per atomic run
    runbook-results.jsonl   # one JSON object per runbook step
    adapted-payloads/       # bundles produced by `adapt --output`
    recon/                  # outputs of `recon` (if you save them here)
    reports/                # rendered findings / navigator / markdown
```

The dir auto-initializes on first write. Override location with `--engagement` per-call or `ATOMIC_ATLAS_ENGAGEMENT_DIR` in `.env` (one folder per customer / scope is the natural pattern). Schema-stable JSONL: each line stamped with `engagement_id`, `recorded_at`, `target_id`, `atomic_path`, plus the full RunResult.

### About findings

`--format findings` aggregates the JSONL into one `Finding` per `(atomic, target)` tuple, with:

- **Verdict**: `VULNERABLE` / `PARTIALLY_VULNERABLE` / `NOT_VULNERABLE` / `INCONCLUSIVE`.
- **Severity**: derived from success rate × evidence richness × atomic frontmatter `severity_floor`.
- **Summary**: 1-2 sentences from the strongest judge reasoning across runs.
- **Evidence**: deduplicated extracted artifacts (e.g., harvested credentials), representative response excerpt.
- **Recommendations**: bullets parsed from the atomic's `## ATLAS mitigations` section.

No new LLM call — fully derived from the data already collected.

---

## `runbook list`

Browse the runbook catalog (chains of atomics tied to a real engagement objective).

```bash
atomic-atlas runbook list [--type <T>] [--tactic <T>] [--json]
```

| Flag | Purpose |
|---|---|
| `--type TEXT` | Filter by runbook type: `dvaa_challenge`, `kill_chain`, `engagement`. |
| `--tactic TEXT` | Filter by ATLAS tactic slug. |
| `--json` | JSON output. |

**Examples:**

```bash
atomic-atlas runbook list
atomic-atlas runbook list --type dvaa_challenge
atomic-atlas runbook list --tactic exfiltration --json
```

---

> Looking for `runbook show` or `runbook validate`? Both were removed in the v0.2 simplification pass. To inspect a runbook, just `cat` the file. To validate, the top-level [`validate`](#validate) auto-detects atomics vs runbooks.

## `runbook exec`

Execute a runbook against a target — walks the DAG, applies on-failure policies, retries where configured, aggregates evidence per step.

```bash
atomic-atlas runbook exec <RUNBOOK_ID_OR_PATH> --target <URL> [--profile <P>] [...]
```

| Flag | Purpose |
|---|---|
| `--target TEXT` | **Required.** Target agent base URL. |
| `--profile PATH` | Target profile YAML. |
| `--output TEXT` | Legacy: write a single JSON file. Prefer `--engagement`. |
| `--engagement PATH` | Engagement directory (default: `./atomic-atlas-engagement/`). Same shape as `exec`. |
| `--authorized` | **Required flag.** |
| `--hitl` | Human-in-the-loop on every outbound. Operator abort propagates. |

**Examples:**

```bash
# Run a DVAA challenge end-to-end against LegacyBot.
atomic-atlas runbook exec RB-DVAA-L1-02 \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --authorized

# Run with HITL — useful for engagement-style work.
atomic-atlas runbook exec RB-DVAA-L1-02 \
  --target http://localhost:7003/v1 \
  --profile targets/dvaa_legacybot.yaml \
  --authorized --hitl
```

The output file (`runbook-results.json` by default) carries per-step results including each step's `evidence_per_run` — the full evidence dict for every run inside every step.

---

## See also

- [`docs/quickstart.md`](quickstart.md) — first run in 10 minutes.
- [`docs/use-cases.md`](use-cases.md) — three end-to-end walkthroughs.
- [`docs/adapt.md`](adapt.md) — payload generator authoring guide.
- [`docs/scoring.md`](scoring.md) — scorer tiers + Evidence schema.
- [`docs/targets.md`](targets.md) — target adapters and profiles.
- [`SPEC.md`](../SPEC.md) — atomic format reference.
