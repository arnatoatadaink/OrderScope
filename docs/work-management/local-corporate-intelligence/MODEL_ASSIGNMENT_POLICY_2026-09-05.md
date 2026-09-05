# OrderScope — Local Corporate Intelligence Model / Agent Assignment Policy

Status: active execution guidance (non-normative)
Date: 2026-09-05
Scope: Local Corporate Intelligence parent WBS and A0 extension

## 1. Purpose

Operational guidance for assigning work to models without changing WBS completion conditions or the Critical Path. Model names are not part of task validity or acceptance semantics; if the model lineup changes, update this document rather than the WBS.

## 2. Model roles

| Model | Primary role | Suitable work | Avoid as sole owner |
|---|---|---|---|
| GPT-5.6 Luna | bounded executor | Narrow implementation, fixture/test additions, routine adapters, mechanical contract propagation, changes under a known specification | Reinterpreting multiple management docs, ambiguous design decisions, integrating several provisional artifacts, Critical Path recalculation |
| GPT-5.6 Terra | integration executor | Multi-file implementation, schema/adapter/test alignment, integration with existing code, medium-scale design, pre-acceptance review | High-impact WBS/CP restructuring without review |
| GPT-5.6 Sol | orchestrator / acceptance reviewer | Cross-reading WBS/CP/Tracker, decomposition, Agent assignment, design boundaries, provisional-result integration, acceptance decisions, conflict resolution | Small mechanical edits can be delegated to Luna/Terra |

## 3. Reasoning effort guidance

Reasoning effort is independent from model suitability.

| Work class | Sol | Terra | Luna |
|---|---|---|---|
| B1: bounded implementation | low | low-medium | medium |
| B2: multi-file implementation | low-medium | medium | high only with tightly specified scope |
| B3: integration / acceptance | medium | high | Do not use as sole owner by default |
| B4: architecture / CP / conflicting evidence | high | high-xhigh | Do not delegate |
| Orchestrator cycle: select task → delegate → review → update Tracker | low if stable; medium for initial audit/conflicts | medium; high when integrating multiple provisional artifacts | Not recommended |

Use `low` only when:
- WBS, CP, and Tracker are already aligned.
- One main task is selected per cycle.
- Parent reviews child output using actual diff/test evidence.
- No new design decision is introduced.
- No provisional artifact is promoted to Accepted unless the gate is already mechanical and explicit.

Otherwise raise effort by one level.

## 4. Assignment rules

1. Read WBS/CP/Tracker and select one task ID first.
2. Check completion conditions, dependencies, and existing artifacts before selecting a model.
3. Luna: normally one Agent = one bounded change set.
4. Terra: may own a coherent schema + implementation + test change across several files.
5. Sol owns decomposition, dependency review, integration review, and Accepted promotion.
6. `Provisional result → Accepted`, Critical Path changes, and schema changes crossing lanes require Sol review.
7. Never fill unknown provider/contract/data semantics by model inference.
8. Record model-selection rationale in the Progress Tracker.

## 5. Parent WBS task suitability

Legend:
- **L** = Luna primary
- **T** = Terra primary
- **S** = Sol primary/review owner
- `L/T` = Luna if bounded; Terra if multi-file
- `T+S` = Terra implementation + Sol acceptance review
- `L/T+S` = bounded implementation by Luna/Terra + Sol acceptance

### W0 — Boundary / Canary / provider governance

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| W0-001 | S | low | Cross-check backlog boundary and Local start gate; decision is already defined |
| W0-002 | T+S | medium | Registry implementation is straightforward; instrument/ticker/CIK/IR identity needs review |
| W0-003 | S | medium | v0.1 scope-boundary decision |
| W0-004 | T+S | medium | Terra builds the checklist; Sol reviews contract exceptions/adoption decisions |

### L0 — Local foundation

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| L0-001 | S | medium | Stack ADR across runtime/storage/API/test and Windows/WSL boundary |
| L0-002 | L | medium | Bounded scaffold/.gitignore change |
| L0-003 | T | medium | Multi-file config/schema/secret/logging-test alignment |
| L0-004 | L/T | medium | Localhost bind + tests; Luna if small |
| L0-005 | T | medium | Migration design and reproducibility |
| L0-006 | T | medium | CLI integration across config/migration/health |

### L1 — Market import / quality

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| L1-001 | T | medium | Manifest/provenance/checksum contract |
| L1-002 | L/T | medium | Importer + idempotency fixture; Luna if boundaries are explicit |
| L1-003 | S | high | Remote change window and stop/resume/catch-up operations |
| L1-004 | T | medium | Deterministic Parquet generation while preserving bar/receipt provenance |
| L1-005 | T+S | medium | Quality rules span multiple dimensions; thresholds/gap semantics need Sol review |
| L1-006 | T | medium | Read-only API integration |

### I0 — Common External Information / Fact contracts

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| I0-001 | T+S | medium | Historical source/entity registry; identity boundary matters |
| I0-002 | T+S | high | Provenance and timestamp semantics affect many downstream tasks |
| I0-003 | T+S | medium | Cursor/checkpoint/pagination/partial/error contract |
| I0-004 | T+S | high | Stable IDs plus update/duplicate/conflict semantics |
| I0-005 | T+S | high | Fact/Evidence/Relationship/Derived/Interpretation separation and provisional integration |
| I0-006 | T+S | medium | Retention/expiry/delete-proof/exception lifecycle |
| I0-007 | L/T+S | high | Test-kit coding can be delegated; formal acceptance spans several upstream contracts |

### S0 — SEC Filing

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| S0-001 | T+S | medium | Terra researches official conditions; Sol reviews adoption constraints |
| S0-002 | T | medium | Bounded incremental provider adapter |
| S0-003 | T | medium | FilingRecord persistence and idempotency |
| S0-004 | L/T+S | medium | Form filter is bounded; Sol only for provisional integration |
| S0-005 | T | medium | Integration with temporary-content lifecycle |
| S0-006 | T+S | high | XBRL unit/period/dimension normalization has difficult semantics |
| S0-007 | T+S | high | Canary acceptance across new/duplicate/amendment/partial cases |

### E0 — Earnings / Fundamental

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| E0-001 | T+S | high | Schedule/result, GAAP/non-GAAP, source/timestamp contract |
| E0-002 | T | medium | Generate candidates from SEC filings |
| E0-003 | T+S | high | SEC/IR dedup and source-priority integration |
| E0-004 | T | medium | Explicit Fact extraction with no gap guessing |
| E0-005 | T+S | high | Company Facts → Dimension → Filing fallback semantics and failure reasons |
| E0-006 | T+S | high | Rename/merge/split/recast identity history is semantically difficult |
| E0-007 | S | high | Multi-quarter, multi-source quality acceptance and unresolved-difference review |

### N0/N1 — News acquisition / Fact extraction

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| N0-001 | S | high | Provider pricing/rights/internal-use comparison and ADR decision |
| N0-002 | T | medium | Metadata adapter implementation |
| N0-003 | T+S | high | Canonical URL, syndication, and update classification semantics |
| N0-004 | T | medium | Temporary body access under the defined lifecycle |
| N1-001 | S | high | Event-taxonomy semantic design |
| N1-002 | L/T | medium | Deterministic baseline; easy to delegate once patterns are fixed |
| N1-003 | T+S | high | Evidence-span/confidence/version and LLM boundary |
| N1-004 | S | high | SEC/IR contradiction, ambiguity, pending-review decisions |
| N1-005 | T+S | medium | Retention controller + compliance review |
| N1-006 | S | high | Recall/lag/misattribution evaluation design and interpretation |

### O0 — Official / policy context

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| O0-001 | T+S | medium | Actor/source identity registry |
| O0-002 | T | medium | Feed adapter implementation |
| O0-003 | T+S | high | Statement/proposal vs signed/implemented Fact-type boundary |
| O0-004 | S | high | Evidence-based direct instrument vs indirect theme relation |
| O0-005 | T+S | high | Quality acceptance across update/delete/identity/relevance |

### X0 — Integration / local observability

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| X0-001 | T+S | high | As-of integration of market/filing/earnings/news/official timeline |
| X0-002 | T | medium | Coverage/health aggregation |
| X0-003 | T | medium | Localhost read-only API integration |
| X0-004 | T+S | high | Scheduler/lock/resume/dry-run across adapters |
| X0-005 | T+S | high | End-to-end deterministic-regeneration acceptance |
| X0-006 | S | high | Operational runbook across credentials/rate/recovery/delete/backup |

## 6. A0 extension task suitability

| Task | Primary | Reasoning | Rationale |
|---|---|---|---|
| A0-001 | S | high | Semantic boundary preventing Cross-Market Rotation from becoming Fact; FX contradiction/confidence rules |
| A0-002 | T+S | high | Terra aligns datasets/calculations; Sol integrates support/contradiction across five hypotheses |

## 7. Current restart assignment

Recommended as of 2026-09-05:
- Orchestrator: **Sol low** for normal cycles.
- Main `I0-002`: **Terra high** for implementation/code inspection, **Sol medium-high** for acceptance review.
- Parallel `L0-002`: **Luna medium**.
- `A0-002` dataset/source definition only: **Terra medium**; add Sol review when hypothesis evaluation begins.

Keep Sol-low orchestration limited to selecting the main task, bounded delegation, diff/test review, and Tracker updates. Raise to medium+ when Sol is making the design decision itself.

## 8. Escalation triggers

Preserve current work and raise parent model/effort by one level if any of the following occurs:
- Schema impact reaches three or more domains, e.g. provenance + Fact Store + A0.
- New work conflicts with an existing provisional artifact.
- WBS completion conditions admit multiple plausible interpretations.
- Tests pass but semantic invariants cannot be established.
- Work involves remote mutation, credentials, retention, or provider contracts.
- An `Accepted` promotion or Critical Path change is proposed.
