# ATLAS Data Snapshot

## Source
- **Dataset:** MITRE ATLAS — Adversarial Threat Landscape for AI Systems
- **Repository:** https://github.com/mitre-atlas/atlas-data
- **Version:** v5.6.0 (most recent tagged release at retrieval time; v5.6.1 is a contribution-schema-only release)
- **Release published:** 2026-05-04
- **Retrieval date:** 2026-05-06
- **Retrieved by:** automated download via `curl` from raw.githubusercontent.com pinned to tag `v5.6.0`

## Files

| File | Source URL | Purpose |
| --- | --- | --- |
| `ATLAS.yaml` | https://raw.githubusercontent.com/mitre-atlas/atlas-data/v5.6.0/dist/ATLAS.yaml | Canonical merged framework data: matrix, tactics, techniques, mitigations, case studies |
| `atlas_output_schema.json` | https://raw.githubusercontent.com/mitre-atlas/atlas-data/v5.6.0/dist/schemas/atlas_output_schema.json | JSON Schema describing the `ATLAS.yaml` output structure |
| `agentic_techniques_extracted.json` | (derived) | Local extraction of techniques flagged as `yes`/`probably` agentic by keyword pass over the v5.6.0 corpus |

## Framework totals (v5.6.0)
- Matrices: 1
- Tactics: 16
- Techniques (incl. sub-techniques): 170
- Distinct top-level technique numbers: 101 (T0000 through T0112)
- Case studies: 57

## Notes on the canonical machine-readable form
- MITRE ATLAS does **not** publish a STIX 2.1 bundle in this repository as of v5.6.0; the merged YAML is the primary distribution.
- The ATLAS Navigator (https://mitre-atlas.github.io/atlas-navigator/) consumes a derivative layer file but the YAML above is the authoritative source.
- The original task pointed at https://atlas.mitre.org/resources/info — that path returns 404 today; the homepage links out to the GitHub repo as the data source.

## License
ATLAS data is published under the same terms as MITRE ATT&CK (see repository LICENSE).
