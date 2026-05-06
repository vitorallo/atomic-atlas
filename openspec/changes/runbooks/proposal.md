# Proposal: Runbooks

## Summary

Introduce **runbooks** as a first-class concept alongside atomics. A runbook is an ordered chain of atomics with engagement-level success criteria, mapped to ATLAS kill-chain stages. Each DVAA challenge becomes one runbook; real-world kill chains (recon → initial-access → cred-access → exfil) become runbooks; custom client-engagement scripts become runbooks. The atomic catalog stays technique-keyed and reusable; runbooks compose those atomics into multi-step assessments.

This resolves a tension in the v0.1 design: some attack patterns (DVAA's "Extract the System Prompt") aren't a single (technique × vector) cell — they're a sequence (recon → cred-access → exfil). Forcing them into one atomic loses the chain semantics; splitting them across multiple atomics loses the engagement intent.

## Why now

1. **DVAA challenges are inherently chained.** 22 challenges map to ~30+ atomics decomposed across techniques. Without runbooks we lose the one-challenge-one-objective framing that makes them teaching artifacts.
2. **ATLAS techniques are tactic-keyed.** ATLAS already groups techniques into 16 tactics (Reconnaissance, Resource Development, Initial Access, …, Impact). A kill-chain is a path through tactics. Runbooks are the natural representation.
3. **The keynote demo is a kill-chain story.** "T0051.001 → T0053 → T0086" was the planned narrative. That's a runbook. Without first-class support, the demo has to manually stitch atomic results.
4. **Practitioners think in engagements, not atomics.** A red-teamer hired for a 2-week assessment writes runbooks (engagement plans) and runs atomics inside them. We should support that workflow directly.

## Proposed solution

```
runbooks/
├── README.md
├── _TEMPLATE/
│   └── runbook_template.md
├── dvaa/                              # one runbook per DVAA challenge
│   ├── L1-01__system-prompt-extraction.md
│   ├── L1-02__api-key-leak.md
│   └── ...
├── kill-chains/                       # canonical ATLAS kill-chain runbooks
│   ├── indirect-pi-to-tool-exfil.md   # T0051.001 → T0053 → T0086
│   ├── rag-poison-to-cred-harvest.md  # T0070 → T0098
│   └── ...
└── engagement/                        # template runbooks for engagements
    ├── customer-support-agent-baseline.md
    └── mcp-deployed-agent-baseline.md
```

A runbook is a markdown file with YAML frontmatter:

```yaml
---
runbook_id: RB-DVAA-L1-01
display_name: System Prompt Extraction
runbook_type: dvaa_challenge          # dvaa_challenge | kill_chain | engagement
target_origin: dvaa-L1-01             # optional; reference back to the source
atlas_tactics:                        # which ATLAS tactics this chain traverses
  - reconnaissance
  - credential_access
atomics:                              # ordered list; each entry is an atomic ref
  - id: 1
    technique: AML.T0098
    vector: direct_chat
    on_failure: stop                  # stop | continue | retry
  - id: 2
    technique: AML.T0083
    vector: direct_chat
    depends_on: [1]
    on_failure: continue
success_criteria: All ordered atomics succeed AND any one of them yields >=50 chars of system-prompt text.
---
```

## Executor

```
atomic-atlas runbook list
atomic-atlas runbook show RB-DVAA-L1-01
atomic-atlas runbook exec RB-DVAA-L1-01 --target <url> --profile <yaml> --authorized
atomic-atlas runbook report --input runbook-results.json --format navigator|markdown
```

`runbook exec` flow:
1. Parse the runbook; resolve each atomic reference against the catalog.
2. Run atomics in order, respecting `depends_on`.
3. After each atomic: check `on_failure` policy; short-circuit on `stop`, retry per policy on `retry`, advance on `continue`.
4. Aggregate results into a `RunbookResult` (atomic-level results + chain-level success).
5. Emit ATLAS Navigator JSON with both the technique cells and the kill-chain edges.

## Why "runbook" not "scenario" or "playbook"

- **Playbook** has connotations from defensive automation (SOAR). Conflicts with the intent.
- **Scenario** is loaded — case studies, training scenarios, etc.
- **Runbook** is operationally neutral: a documented sequence of steps an operator runs. Matches Atomic Red Team's language. Practitioners get it instantly.

## Non-goals

- **Not a workflow engine.** No conditional branches based on response content, no LLM-driven path selection. Sequential or DAG-ordered atomics with simple `on_failure` policies. Anything more complex belongs in the agent runner skill, not the CLI executor.
- **Not a replacement for atomics.** Atomics remain the unit of test. Runbooks compose them.
- **Not an engagement management tool.** No timeline tracking, no client metadata, no scoping documents. Just the technical chain.

## Scope

**v0.2.** Ships alongside Lobster and the v0.2 catalog expansion. v0.1 keynote demo can stay atomics-direct; the chain narrative becomes a runbook in v0.2.

## Status

- [ ] proposal + specs + tasks (this change)
- [ ] `runbooks/` directory with `_TEMPLATE/runbook_template.md`
- [ ] JSON Schema for runbook frontmatter
- [ ] Parser support: `atomic_atlas.runbook.load`, `atomic_atlas.runbook.load_all`
- [ ] CLI: `atomic-atlas runbook list / show / exec / report`
- [ ] Executor: sequential + DAG-ordered, on-failure policies
- [ ] `RunbookResult` schema added to results.json shape
- [ ] DVAA challenges harvested as 22 runbooks under `runbooks/dvaa/` (the inline mapping work that the blocked subagent didn't get to do)
- [ ] First 3-5 canonical ATLAS kill-chain runbooks under `runbooks/kill-chains/`

## Open questions

1. **Runbook GUIDs.** Same UUID4 convention as atomics? Recommended yes — one ID space for both (run an atomic by GUID, run a runbook by GUID; never collide because GUIDs are random).
2. **Atomic refs by GUID or by `<technique>/<vector>`?** Path-based is human-readable; GUID-based is rename-stable. Recommended: support both, prefer path in fresh runbooks (humans write them).
3. **Parallelism.** Allow `parallel_with` so two atomics can run simultaneously (e.g., recon-style atomics). Recommended yes — small surface, big win for engagement-style runbooks. Schema-only in v0.2; executor still serializes; v0.3 adds real concurrency.
4. **Cross-target runbooks.** Some kill chains span multiple targets (compromise agent A, pivot to agent B). Recommended yes for v0.3 — needs `target_overrides` per atomic.
