# Tasks: Atomic Format

## Completed (v0.1)
- [x] SPEC.md (format reference) — including the `unclassified/` convention
- [x] `schema/atomic_frontmatter.schema.json` — accepts both `AML.TXXXX[.SUB]` and `UNCLASSIFIED.<slug>` patterns
- [x] `src/atomic_atlas/parser.py` — `load`, `load_all`, frontmatter validation, optional `payload:` field, skips `_TEMPLATE/`, `payloads/`, and README/CHANGELOG/CONTRIBUTING files
- [x] `atomics/_TEMPLATE/vector_template.md` — contributor template
- [x] UUID4 variant nibble fixes (T0065, T0098, T0099, T0104)
- [x] **Catalog grew from 12 → 27 atomics** during the v0.1 DVAA harvest:
  - New techniques covered: T0011.002, T0054, T0080, T0080.000, T0083, T0084, T0097, T0110, T0112
  - New vectors on existing techniques: T0099/mcp_server, T0086/a2a_message, T0108/mcp_server + T0108/a2a_message, T0051.001/a2a_message
  - First `UNCLASSIFIED.<slug>` atomic: `unclassified/self-replicating-memory/direct_chat.md`
- [x] `atomics/unclassified/README.md` documents the convention
- [x] `index.yaml` auto-catalog of all atomics

## Pending (v0.2)
- [ ] Add CI: GitHub Actions workflow running `atomic-atlas validate` + `atomic-atlas runbook validate` on every PR
- [ ] Add `last_verified_date` field to schema (for model drift tracking)
- [ ] Add `payload_sha256` validation in parser (verify payload files match declared hash)
- [ ] Optional `success_indicators` frontmatter field (replace prose-as-substring scorer with explicit indicator list — see runbook task #39)
