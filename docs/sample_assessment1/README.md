# sample_assessment1 — recorded engagement artifacts

A **real** atomic-atlas engagement captured live against a local DVAA
LegacyBot, committed verbatim so you can see actual output without running
anything. Nothing here is synthetic. The walkthrough is
[`docs/sample_execution.md`](../sample_execution.md).

| File | What it is |
|---|---|
| `results.jsonl` | Raw engagement memory — the exact JSONL `atomic-atlas exec` appended (one `atomic_result` entry, 5 runs, full per-run `evidence`). |
| `reports/findings.md` | `report --format findings` — stakeholder verdict/severity aggregation. |
| `reports/run-report.md` | `report --format markdown` — per-run transcript excerpts, scorer tier, judge reasoning, extracted artifacts. |
| `reports/navigator.layer.json` | `report --format navigator` — MITRE ATLAS Navigator layer (import at navigator.mitre.org). |
| `reports/coverage.txt` | `report --format coverage` — technique × vector matrix with the live success rate. |
| `recon/dvaa_legacybot.recon.txt` | `recon` output — entry-vector + guardrail fingerprint of the target. |

## Regenerate

DVAA LegacyBot on `localhost:7003`, PyRIT installed (`pip install -e
'.[orchestrator]'`, Python 3.10–3.13), LLM config in `.env`:

```bash
atomic-atlas recon --target http://localhost:7003/v1 \
  > docs/sample_assessment1/recon/dvaa_legacybot.recon.txt
atomic-atlas exec AML.T0083/direct_chat \
  --profile targets/dvaa_legacybot.yaml --authorized \
  --engagement docs/sample_assessment1
atomic-atlas report --engagement docs/sample_assessment1 --format findings \
  --output docs/sample_assessment1/reports/findings.md
atomic-atlas report --engagement docs/sample_assessment1 --format markdown \
  --output docs/sample_assessment1/reports/run-report.md
atomic-atlas report --engagement docs/sample_assessment1 --format navigator \
  --output docs/sample_assessment1/reports/navigator.layer.json
atomic-atlas report --engagement docs/sample_assessment1 --format coverage \
  > docs/sample_assessment1/reports/coverage.txt
```

Output is non-deterministic (live LLM target + attacker LLM) — a re-run will
not byte-match this capture, but the verdict and extracted-artifact shape
hold. This directory is force-tracked via a `.gitignore` negation; the global
`*.layer.json` / `*.results.json` artifact ignores would otherwise drop it.
