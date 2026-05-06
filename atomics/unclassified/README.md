# `unclassified/` — atomics that don't yet map to an ATLAS technique

ATLAS-keyed atomics live under `atomics/AML.TXXXX/<vector>.md`. This directory holds atomics whose attack pattern is **real and worth testing**, but for which no MITRE ATLAS technique ID currently exists. Once ATLAS publishes a matching technique, the atomic moves out of `unclassified/` to its `AML.TXXXX/` home.

## Why we keep them

- The ATLAS framework is moving fast — agentic techniques are being added with each release. Atomics that anticipate a technique still have practitioner value.
- Some attack patterns are real-world but novel enough that no ATLAS submission has landed yet.
- Better to capture the test idea now than lose it.

## Convention

Each unclassified atomic lives at:

```
atomics/unclassified/<slug>/<vector>.md
```

`<slug>` is a kebab-case label (e.g., `scope-violation`, `chain-hijack-a2a`).

The frontmatter `atlas_technique` field uses the form `UNCLASSIFIED.<slug>` and the parent directory name MUST match the slug:

```yaml
---
atlas_technique: UNCLASSIFIED.scope-violation
display_name: Agent Scope Violation
interaction_vector: direct_chat
guid: ...
---
```

## What goes here vs. what doesn't

**Goes here:**
- An attack pattern with no current ATLAS technique that exercises the same intent.
- A decomposition of a real-world incident that doesn't fit cleanly under an existing technique.
- A multi-technique chain where the chain itself has no ATLAS-keyed parent.

**Does NOT go here:**
- An attack that maps to an existing ATLAS technique, even imperfectly. Use the closest ATLAS technique and document the imperfection in the atomic body.
- A vendor-specific bug. Atomics are technique-keyed, not target-keyed; vendor specifics belong in the target profile.
- An idea that hasn't been verified against the latest ATLAS release. Always check `data/atlas/ATLAS.yaml` before adding here.

## When ATLAS catches up

When MITRE publishes a technique that fits an unclassified atomic:

1. Move the file: `atomics/unclassified/<slug>/<vector>.md` → `atomics/AML.TXXXX/<vector>.md`
2. Update frontmatter: `atlas_technique: AML.TXXXX`, keep the same `guid` (stable identity across renames)
3. Add a `## Provenance` note in the body if the atomic was an early take on the technique

## Current contents

| Slug | Display name | Reason |
|---|---|---|
| (none yet) | | |

This list will grow as the v0.2 catalog expansion proceeds.
