# How atomic-atlas uses PyRIT

atomic-atlas is a **PyRIT extension, not a re-implementation**. Microsoft
[PyRIT](https://github.com/Azure/PyRIT) is the orchestration backbone for
`atomic-atlas exec`: it owns the attack loop, the attacker-LLM mutation, the
scoring graph, and conversation memory. atomic-atlas contributes the parts PyRIT
does not have — the **12 agentic delivery vectors**, **ATLAS technique keying**,
the **two-tier scorer + Evidence**, the **`adapt` payload generator**, and the
**engagement / Finding** layer.

This document states the dependency precisely: *why* we need PyRIT, *exactly
what* we call, and *what we deliberately don't take from it*.

---

## 1. Why PyRIT (and why an extension, not a fork)

`atomic-atlas exec` has to:

1. take an attack objective and **mutate it across multiple turns** using an
   attacker LLM until the target succumbs or runs out of turns,
2. send each turn through a **pluggable target abstraction**,
3. **score** every response with an LLM judge, and
4. keep **conversation memory** so multi-turn context is coherent.

PyRIT already does all four well, for HTTP/chat targets. Re-implementing them
would be wasted effort and would diverge from a tool the AI-red-team community
already trusts. So atomic-atlas plugs into PyRIT at four seams and adds the
**agentic delivery dimension PyRIT lacks**: a poisoned RAG document, an MCP tool
registration, an intercepted tool response, an uploaded file, an inbound
webhook — none of which PyRIT models natively.

The design principle (see [`SPEC.md`](../SPEC.md)): **intent over
implementation**. The atomic describes *what* the attack does; PyRIT + our
target subclasses figure out *how* to deliver it.

---

## 2. PyRIT is an *optional* runtime dependency

| Install | PyRIT pulled in? | What runs |
|---|---|---|
| `pip install atomic-atlas` | **No** | `list` · `recon` · `report` · `validate` · MCP server |
| `pip install 'atomic-atlas[orchestrator]'` | **Yes** | the above **+ `exec`** (run atomics against a target) |

**Why optional:** PyRIT's transitive deps (`azure-ai-*`, `openai`, `anthropic`,
`chromadb`, `accelerate`, `transformers`, …) total 1+ GB. Atomic authoring,
catalog validation, recon, reporting, and the MCP server need none of it —
forcing that install on every contributor or CI job would be wasteful.

**How it stays optional in the code:**

- Every `pyrit` import is **function-local / lazy** — never at module top level.
  Importing any atomic-atlas module without PyRIT installed succeeds.
- The target base class degrades safely
  (`src/atomic_atlas/targets/base.py`):

  ```python
  try:
      from pyrit.prompt_target import PromptTarget
      PYRIT_AVAILABLE = True
  except ImportError:
      PromptTarget = object          # base class falls back to object
      PYRIT_AVAILABLE = False

  class AtomicAtlasTarget(PromptTarget):
      def __init__(self, ...):
          require_pyrit()            # raises PyRITNotInstalledError here
  ```

- `require_pyrit()` raises `PyRITNotInstalledError` with the exact install hint
  the moment a PyRIT-requiring path is hit (`exec`, target instantiation, judge
  scorer build) — not as an opaque `ImportError` deep in a stack trace.

---

## 3. Version requirement — and a caveat to know

| | |
|---|---|
| Declared pin (`pyproject.toml`) | `pyrit>=0.5.0` (under the `[orchestrator]` extra) |
| Version the code is written against | **0.13.x** (currently installed: `0.13.0`) |
| Python | PyRIT 0.13 supports **3.10–3.13**; **not** 3.14 |

**Caveat:** the declared pin (`>=0.5.0`) is **looser than the code requires**.
atomic-atlas imports the `pyrit.executor.attack.*` namespace
(`PromptSendingAttack`, `RedTeamingAttack`, `AttackScoringConfig`,
`AttackAdversarialConfig`, `AttackOutcome`) and the
`pyrit.score.true_false.*` modules — these are the **0.11+ "attacks" API** that
replaced the old `pyrit.orchestrator` API. On a resolved `pyrit==0.5.x` install,
`atomic-atlas exec` would fail with an `ImportError` at runtime. Treat
**`pyrit>=0.13,<0.14`** as the real supported range; tightening the pin in
`pyproject.toml` is a tracked follow-up.

---

## 4. Exactly what we use from PyRIT

Every symbol atomic-atlas imports from PyRIT, why, and where:

| PyRIT symbol | What atomic-atlas uses it for | Where |
|---|---|---|
| `pyrit.prompt_target.PromptTarget` | Base class for **every agentic vector target**. `AtomicAtlasTarget` extends it with ATLAS metadata + `setup()`/`cleanup()` lifecycle. | `targets/base.py` |
| `pyrit.prompt_target.OpenAIChatTarget` | The **attacker LLM and the judge LLM**; also wrapped directly by `DirectChatTarget` for the `direct_chat` vector. Endpoint/key are env-driven so OpenRouter / Ollama / vLLM / LiteLLM all work. | `llm.py`, `targets/direct_chat.py` |
| `pyrit.models.construct_response_from_request` | Builds a PyRIT-shaped response object so a **non-HTTP vector** (poisoned RAG, MCP tool, tool response, uploaded doc, webhook, HITL) can hand a result back into PyRIT's loop. | `targets/{rag_corpus,mcp_server,tool_response,document_upload,webhook}.py`, `hitl.py` |
| `pyrit.executor.attack.single_turn.PromptSendingAttack` | **Single-turn / deterministic** send — used for `multi_turn:false` atomics and as the offline fallback when no attacker LLM is reachable. | `runner.py` |
| `pyrit.executor.attack.multi_turn.RedTeamingAttack` + `core.attack_config.AttackAdversarialConfig` | **Multi-turn attacker-LLM mutation** — the attacker rewrites the seed each turn. We inject the profile's `target_context` into the attacker's system prompt so mutations are domain-aware. | `runner.py` |
| `pyrit.executor.attack.core.attack_config.AttackScoringConfig` | Wires our objective scorer into the attack. | `runner.py` |
| `pyrit.executor.attack.core.attack_strategy.AttackOutcome` | Read the attack's terminal outcome to set the run verdict. | `runner.py` |
| `pyrit.score` — `SelfAskTrueFalseScorer`, `TrueFalseScorer`, `TrueFalseScoreAggregator`, `ScorerPromptValidator`; `pyrit.score.true_false.self_ask_true_false_scorer.TrueFalseQuestion` | The **LLM judge tier** wraps these. The atomic's `## Success criteria` (+ optional `judge_guidance`/`judge_examples`) becomes the true/false question. | `scorers.py` |
| `pyrit.models.Score`, `pyrit.models.MessagePiece` | Scorer I/O; we attach atomic-atlas `Evidence` onto PyRIT's `Score.score_metadata` channel (no PyRIT modification). | `scorers.py` |
| `pyrit.memory.CentralMemory`, `pyrit.memory.SQLiteMemory` | Conversation memory PyRIT requires. We default to **in-memory SQLite** (`:memory:`) — ephemeral, right for one-shot `exec`. Override with `ATOMIC_ATLAS_PYRIT_DB`. | `runner.py` |

> Note: `llm.complete()` (used by `adapt`) deliberately **bypasses** PyRIT and
> calls the `openai` SDK directly — payload adaptation needs no Score/Memory
> graph, so loading PyRIT there would be pure overhead.

---

## 5. What we deliberately do **not** take from PyRIT

- **PyRIT's datasets / built-in prompt catalog** — atomic-atlas's catalog is the
  filesystem (`atomics/<ATLAS-id>/<vector>.md`); the atomic *is* the source of
  truth.
- **PyRIT's broader orchestrator zoo** — only the two attack classes above are
  used. Everything else (technique keying, the 12-vector taxonomy, the
  two-tier scorer + Evidence, `adapt`, engagement memory, Findings, Navigator
  output) is atomic-atlas's own layer on top.
- **PyRIT's scoring verdict as the final word** — PyRIT's judge is one of three
  tiers (judge → indicators → deterministic substring). The tier actually used
  is recorded in `Evidence`; there is no silent downgrade. See
  [`docs/scoring.md`](scoring.md).

---

## 6. The seam, end to end

```
atomic .md (intent)                          ← atomic-atlas (parser)
   │  optional: adapt → target-tuned payload  ← atomic-atlas (llm.complete, no PyRIT)
   ▼
PyRIT attack                                  ← PyRIT
   ├─ multi_turn:true  + attacker LLM  → RedTeamingAttack (+ target_context)
   └─ multi_turn:false / offline       → PromptSendingAttack
   ▼
AtomicAtlasTarget subclass                    ← atomic-atlas (the agentic vector)
   rag_corpus · mcp_server · tool_response · document_upload · webhook · direct_chat …
   ▼
real target agent (e.g. DVAA)
   ▼
PyRIT Score  ─── attach Evidence ───────────▶ atomic-atlas Evidence    ← atomic-atlas
   ▼
RunResult → engagement JSONL → Finding        ← atomic-atlas (report --format findings)
```

PyRIT owns the middle band (attack loop + score + memory). atomic-atlas owns
both ends (intent in, evidence-shaped finding out) **and** the target band — the
agentic delivery vectors are the whole reason this project exists.

---

## 7. Graceful degradation summary

| Condition | Behaviour |
|---|---|
| PyRIT not installed | `list`/`recon`/`report`/`validate`/MCP work; `exec` raises `PyRITNotInstalledError` with the install hint |
| PyRIT installed, no `OPENAI_API_KEY` (or `ATOMIC_ATLAS_OFFLINE=1`) | `RedTeamingAttack` → `PromptSendingAttack` fallback, logged with a warning; no attacker-LLM mutation |
| PyRIT installed, judge LLM unreachable | Scorer falls back judge → indicators → substring; tier recorded in `Evidence` |
| Persistent PyRIT memory wanted | Set `ATOMIC_ATLAS_PYRIT_DB=/path.db` or call `CentralMemory.set_memory_instance()` before invoking the runner |

---

*See also: [`docs/install.md`](install.md) (install matrix + troubleshooting),
[`docs/scoring.md`](scoring.md) (the three scorer tiers + Evidence schema),
[`docs/targets.md`](targets.md) (target profiles + `target_context`),
[`SPEC.md`](../SPEC.md) (atomic format + design principles).*
