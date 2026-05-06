# Tasks: Atomic Format

## Completed
- [x] Write SPEC.md (format reference)
- [x] Write schema/atomic_frontmatter.schema.json
- [x] Write src/atomic_atlas/parser.py
- [x] Write 12 seed atomics across 9 techniques
- [x] Fix UUID4 variant nibbles in T0065, T0098, T0099, T0104

## In progress
- [ ] Write atomics/_TEMPLATE/vector_template.md
- [ ] Write index.yaml (auto-catalog of all atomics)

## Pending
- [ ] Add CI: GitHub Actions workflow running `atomic-atlas validate` on every PR
- [ ] Add `last_verified_date` field to schema (for model drift tracking, v0.2)
- [ ] Add `payload_sha256` validation in parser (verify payload files match declared hash)
