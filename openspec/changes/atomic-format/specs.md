# Specs: Atomic Format

## Frontmatter schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `atlas_technique` | string | ✓ | Pattern: `AML.T[0-9]{4}(\.[0-9]{3})?` |
| `display_name` | string | ✓ | Human-readable technique name |
| `interaction_vector` | enum | ✓ | One of 12 defined vectors |
| `guid` | string | ✓ | UUID4 — stable across renames |
| `runs` | integer | — | Default 5; range 1–50 |
| `target_requires` | array | — | List of `{capability: str}` |
| `pyrit_orchestrator` | enum | — | Default `PromptSendingOrchestrator` |
| `pyrit_scorer` | string | — | Default `SubStringScorer` |

## Body sections (H2 headings)

| Section | Required | Content type |
|---|---|---|
| `## Why this matters` | recommended | 1–2 sentence prose; write for a CISO |
| `## Prerequisites` | recommended | Bullet list of attacker/target capabilities |
| `## Attack strategy` | recommended | Prose + payload file reference |
| `## Interaction` | recommended | Numbered steps (setup, trigger, observe) |
| `## Success criteria` | recommended | Plain prose; used by LLM judge |
| `## ATLAS mitigations` | optional | Bullet list of `MXXX: name` |
| `## Cleanup` | recommended | Bullet list of cleanup actions |

## Vector enum (12 values)

`direct_chat`, `system_prompt`, `rag_corpus`, `document_upload`, `tool_response`, `mcp_server`, `web_fetch`, `webhook`, `email`, `a2a_message`, `computer_use`, `model_api`

## Directory layout

```
atomics/
  <AML.TXXXX>/
    <vector>.md          ← one atomic per (technique, vector) cell
    payloads/
      <payload-name>.md  ← seed payload files (ignored by parser)
      <payload-name>.json
```

## Validation rules (enforced by JSON Schema + parser)

1. `atlas_technique` must match the parent directory name
2. `guid` must be unique across all atomics in the repo
3. `interaction_vector` must be one of the 12 defined values
4. Payload files referenced in `## Attack strategy` must exist under `payloads/`
5. Files in `payloads/` are excluded from atomic loading

## Parser contract

`load(path, validate=True) → AtomicTest`  
`load_all(atomics_dir) → list[AtomicTest]`  
`AtomicTest.section(name) → str`

Parser skips files whose path contains a `payloads/` component.  
Parser raises `ValueError` on missing frontmatter or schema validation failure.
