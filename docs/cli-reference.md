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
| `--model TEXT` | Override generator LLM model (default: `ATOMIC_ATLAS_ADAPTER_MODEL` or `gpt-4o`). |
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

# Cheaper model for iteration.
atomic-atlas adapt AML.T0083/direct_chat \
  --profile targets/dvaa_legacybot.yaml \
  --model gpt-4o-mini --output adapted.md

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
| `--output TEXT` | Output file for results JSON (default: `results.json`; appends if exists). |
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
| `OPENAI_API_KEY` | Required for the LLM judge tier and for `RedTeamingOrchestrator`'s attacker LLM. |
| `OPENAI_API_BASE` | OpenAI-compatible proxy (LiteLLM, vLLM). |
| `ATOMIC_ATLAS_LLM_MODEL` | LLM model name used by the judge, attacker, and adapter (default `gpt-4o`). |
| `ATOMIC_ATLAS_OFFLINE=1` | Disable every LLM call site (judge tier, attacker LLM, adapter). Forces deterministic indicator scoring + `PromptSendingAttack`. |

A few additional vars exist for tests / development (`ATOMIC_ATLAS_ATOMICS_DIR`, `ATOMIC_ATLAS_SKIP_DOTENV`, `ATOMIC_ATLAS_PYRIT_DB`, `ATOMIC_ATLAS_EVIDENCE_SNIPPET_MAX`); they're stable but not part of the operator surface.

See [`docs/scoring.md`](scoring.md) for the scorer-tier details.

---

## `report`

Render results from `exec` into a Navigator layer, coverage matrix, or evidence-rich markdown.

```bash
atomic-atlas report --input <FILE> --format <FMT> [--output <FILE>]
```

| Flag | Purpose |
|---|---|
| `--input PATH` | **Required.** `results.json` from `exec`. |
| `--format navigator\|coverage\|markdown` | Output format. Default: `navigator`. |
| `--output TEXT` | Write to file (default: stdout). |

**Examples:**

```bash
# ATLAS Navigator JSON layer (open at https://mitre-atlas.github.io/atlas-navigator/)
atomic-atlas report --input results.json --format navigator --output dvaa.layer.json

# Compact coverage matrix in the terminal.
atomic-atlas report --input results.json --format coverage

# Markdown report with per-run evidence inline.
atomic-atlas report --input results.json --format markdown --output report.md
```

The markdown format renders the evidence dict per run — `tier`, judge reasoning, matched indicators, extracted artifacts. Useful for sharing with stakeholders.

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
| `--output TEXT` | Output file (default: `runbook-results.json`). |
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
