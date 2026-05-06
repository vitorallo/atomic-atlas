# Specs: CLI and Reporting

## CLI interface

```
atomic-atlas recon --target <url> [--auth-header <value>]
atomic-atlas exec <technique/vector> --target <url> [--profile <yaml>] [--runs N] [--output <file>] --authorized
atomic-atlas report --input <results.json> --format navigator|coverage|markdown [--output <file>]
atomic-atlas validate [<atomic_path>]
```

### recon
- Probes: direct_chat (POST /v1/chat/completions), tool exposure (/openapi.json, /api/tools, /v1/tools), RAG (keyword probe), MCP (/.well-known/mcp, /mcp), webhook (/webhook, /hooks, /inbound)
- Guardrail fingerprinting: sends 3 probe phrases; detects input filter by refusal pattern
- Output: text report to stdout; suggested technique list

### exec
- `atomic_path`: resolved as `atomics/<path>.md` if not an absolute path
- Requires `--authorized` flag; exits with error if absent
- Loads target profile YAML if `--profile` given; merges `base_url` from `--target`
- Appends to `results.json` (creates if absent)
- Exit code 0 if ≥1 success across runs; exit code 1 if all runs fail or error

### report
- `navigator`: JSON object with `name`, `versions`, `domain`, `techniques[]`, `gradient`, `legendItems`
- `coverage`: terminal table, technique × vector, symbols: `●`=atomic+result, `○`=atomic only, `·`=none
- `markdown`: `## Technique / Vector` sections with success rate

### validate
- Loads all atomics under `atomics/` (or the specified path)
- Runs JSON Schema validation on each frontmatter
- Prints `✓ path` or `✗ path: error`; exits non-zero if any failures

## ATLAS Navigator layer schema

```json
{
  "name": "atomic-atlas coverage",
  "versions": {"attack": "14", "navigator": "4.9", "layer": "4.5"},
  "domain": "mitre-atlas",
  "techniques": [
    {
      "techniqueID": "T0051.001",
      "color": "#ff<gb>",
      "comment": "Vector: rag_corpus | 4/5 runs succeeded (80%)",
      "metadata": [
        {"name": "vector", "value": "rag_corpus"},
        {"name": "success_rate", "value": "0.80"},
        {"name": "guid", "value": "<uuid>"}
      ]
    }
  ]
}
```

## RunResult schema (results.json entries)

```json
{
  "atomic_path": "atomics/AML.T0051.001/rag_corpus.md",
  "atlas_technique": "AML.T0051.001",
  "interaction_vector": "rag_corpus",
  "guid": "<uuid>",
  "total_runs": 5,
  "successes": 4,
  "failures": 1,
  "errors": 0,
  "duration_seconds": 12.3,
  "run_details": [{"run": 1, "success": true, "response_preview": "..."}]
}
```

## Claude Code skill interface

Invocation: `/atomic-atlas exec <technique/vector> --target <url>`

Steps:
1. Load atomic markdown (Read tool)
2. Recon target (Bash: `atomic-atlas recon` or direct HTTP probes)
3. Reason about delivery for the specific target implementation
4. Generate payload variant (adapted to target context)
5. Execute interaction turns
6. Evaluate success against `## Success criteria` prose
7. Cleanup
8. Report: technique, vector, success rate, ATLAS Navigator JSON

Authorization prompt: "Confirm you have written authorization to test [url]?"

## recon.py contract

```python
async def recon(target_url: str, auth_headers: dict | None) -> ReconResult
```

`ReconResult.print_report()` → formatted terminal output  
`ReconResult.suggested_techniques` → list of ATLAS technique IDs
