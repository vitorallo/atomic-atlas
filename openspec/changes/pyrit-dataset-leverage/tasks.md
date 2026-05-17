# Tasks: PyRIT Dataset Leverage

## Decision-only (this change)

- [x] Inventory PyRIT 0.13 bundled datasets (read-only) — recorded in `proposal.md`
- [x] Cross-check the 17 uncovered high-confidence agentic techniques against
      `data/atlas/agentic_techniques_extracted.json` vs `atomics/` (2026-05-17)
- [x] Record the **describe + cite, no copy** principle (`specs.md`)
- [x] Record the PyRIT / atomic-atlas / MITRE licensing posture (`proposal.md`)
- [x] Add root `LICENSE` (MIT, `Copyright (c) 2026 Vito Rallo and atomic-atlas contributors`)

## Deferred — separate future change, NOT done here

- [ ] Enrich `AML.T0054/direct_chat.md` + `payloads/jailbreak_seed.md` —
      broader variant-family shapes + sharper judge guidance, citing PyRIT taxonomy
- [ ] Same enrichment for `AML.T0051.000`, `AML.T0051.001`, `AML.T0065`
- [ ] (Optional) ≤2 net-new atomics with clean ATLAS mapping:
      many-shot / in-context poisoning; encoding/cipher evasion
- [ ] (Optional) `CONTRIBUTING.md` with DCO `Signed-off-by` — forward-insurance
      for a clean whole-project relicense (e.g. → Apache-2.0 under a future
      MITRE program); not required for MITRE incorporation
- [ ] (Conditional) `THIRD_PARTY.md` — only if any permissive corpus is ever
      vendored; not needed today

> Implementation of the deferred items is intentionally out of scope for this
> change. This change is the decision record only.
