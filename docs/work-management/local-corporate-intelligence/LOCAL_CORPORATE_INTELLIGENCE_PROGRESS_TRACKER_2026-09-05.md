# OrderScope — Local Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-05
Parent WBS: `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Extension WBS: `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Model assignment: `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
Runtime-status authority: **this file**

## 1. Purpose and authority

This file is the sole integrated authority for Local Corporate Intelligence runtime progress. Track current status, accepted/provisional/ready/blocked state, restart point, execution evidence, unresolved items, and next safe action here.

The Parent WBS defines what must be completed. The Integrated Critical Path defines static dependency structure, permanent gates, and safe parallelization. Neither should be updated merely because execution progressed.

Model/Agent selection follows the Model Assignment Policy and must be recorded per cycle.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Accepted | WBS completion conditions and dependencies are satisfied; safe as a downstream prerequisite |
| In progress | Currently being implemented or reconciled |
| Provisional result | Artifact exists, but an upstream dependency or formal acceptance is pending |
| Ready | Dependencies are satisfied; safe to start |
| Blocked | Waiting on an external window, unresolved contract, or upstream result |
| Not started | Dependency gate is closed or work has not started |

## 3. Current critical-path snapshot

| Task | Status | Evidence / interpretation | Next action |
|---|---|---|---|
| I0-001 | Accepted | The prerequisite for I0-002 was satisfied before the current execution cycles | Reference only during downstream reconciliation |
| I0-002 | Accepted | Immutable types and contract tests fix the source ref/hash, source timestamp, retrieved/available/internal-accepted timestamps, and provider revision; parent diff/test/semantic review completed in the 2026-09-05 execution cycle | Reference only during downstream reconciliation |
| I0-003 | Accepted | Persistable types and tests fix provider/source scope, bounded windows, opaque cursors, and resumable partial/error states; parent diff/test/semantic review completed in the 2026-09-05 execution cycle | Reference only when connecting I0-007 |
| I0-004 | Ready | Dependency satisfied by `I0-002` acceptance | Implement as a separate cycle |
| I0-005 | Provisional result | Fact Store logical schema exists; alignment to I0-002 provenance types and formal acceptance remain | Reconcile and formally accept in a separate cycle |
| I0-006 | Not started | Depends on `I0-005` | Define the temporary-content lifecycle after I0-005 is Accepted |
| I0-007 | Provisional result | Common contract-test kit exists; formal acceptance waits for I0-003/004/006 | Connect the upstream contracts and formally accept |
| S0-002 | Not started | Gated by I0-007 formal acceptance and S0-001 | Start the SEC adapter after I0-007 is Accepted |
| S0-003 | Not started | Depends on `S0-002` | Implement FilingRecord persistence |
| S0-004 | Provisional result | Form-filter implementation/report exists but is not yet connected to S0-003 | Confirm integration after S0-003 and preserve acceptance evidence |
| S0-005 | Not started | Depends on `S0-003` + `I0-006` | Implement temporary filing-document content handling |
| S0-006 | Not started | Depends on `S0-003` | Implement the Company Facts/XBRL adapter |
| S0-007 | Provisional result | Early validation evidence may exist; WBS acceptance testing follows S0-004..006 integration | Run formal Canary acceptance after integration |
| E0-001..007 | Not started | Depends on the S0 lane and I0-005 | Start sequentially after S0-007 |
| N1 / O0 / X0 | Not started | Depends on the Core Fact/SEC/Earnings lanes | Start later on the Core CP |

## 4. Parallel lanes

### Lane A — Core contracts

Latest accepted task: `I0-003`. Next safe main task: `I0-004`.

Static dependency order is defined in the Critical Path; this section records only the current runtime position.

### Lane B — Local foundation

`L0-002` is Accepted. Next safe dependent work is one of `L0-003`, `L0-004`, or `L0-005`, subject to task/file-overlap review.

`L1-003` remains blocked by the separately approved `SMOKE-007` change window and does not block fixture work.

### Lane C — Cross-Market extension

| Task | Status | Next action |
|---|---|---|
| A0-001 | Provisional result | Design complete; wait for I0-005 acceptance, then reflect fields/schema/fixtures |
| A0-002 | Not started | Dataset/source definition may proceed before final schema write |

### Lane D — SEC / Earnings

Blocked until `I0-007` formal acceptance.

## 5. Current model / Agent assignment

| Role / task | Assignment | Reasoning | Note |
|---|---|---|---|
| Orchestrator | Sol | low | Normal cycle while WBS/CP/Tracker are aligned; raise to medium+ for design or Accepted promotion |
| I0-004 implementation | Terra | high | Stable identity/update/duplicate/conflict semantics affect downstream contracts |
| I0-004 acceptance review | Sol | medium-high | Verify semantic boundary and downstream compatibility |
| Local-foundation bounded work | Luna/Terra | per Model Assignment Policy | Select one Ready task only |
| A0-002 dataset/source definition | Terra | medium | No final schema write or hypothesis integration yet |

Record the actual model, reasoning effort, delegation rationale, and review result at the end of each cycle.

## 6. Known non-blockers / deferred items

- `L1-003` remote D1 export change window is deferred and does not block local fixture work.
- `A0-002` is a validation lane and is not currently a serial blocker for Core Corporate Intelligence.
- Preserve and reconcile provisional artifacts for `I0-005`, `I0-007`, and `S0-004`; do not discard them.

## 7. Current restart rule

- Main local session: `I0-004`
- Second parallel local session: choose one Ready Local-foundation task (`L0-003`, `L0-004`, or `L0-005`) after overlap review
- Cross-Market session: `A0-002` dataset/source definition only until `I0-005` is Accepted
- SEC implementation waits for `I0-007` formal acceptance

## 8. Unresolved items

- Analyst Consensus as-of history provider and contract conditions
- AI/Semiconductor proxy definition for A0-002
- short/borrow data provider for H4 validation
- whether A0-002 becomes mandatory for v0.1 release acceptance
- exact evidence needed to promote provisional `I0-005`, `I0-007`, and `S0-004/S0-007` artifacts after dependency integration

Do not infer unresolved values; update this tracker only from repository evidence, test results, or confirmed external contract/source information.

## 9. L0-002 execution cycle (2026-09-05)

| Item | Result |
|---|---|
| Task ID | `L0-002` |
| Model / reasoning | `gpt-5.6-luna` / medium |
| Selection rationale | Model policy assigns Luna/medium to the bounded scaffold and `.gitignore` change; no cross-lane design or acceptance decision was made. |
| Changed files | `analysis/config/README.md` (new scaffold marker), `pyproject.toml`, `uv.lock`, and this Progress Tracker; `var/` was verified Git-ignored (existing rule retained). |
| Tests / checks | Executor and parent review each ran `uv sync --locked` and `uv run pytest -q` — **58 passed**. Parent review also verified the three scaffold directories, `var/` exclusion, and `git diff --check`. |
| Completion criteria | WBS L0-002 criteria satisfied: all three analysis scaffold directories are present and `var/` is outside Git scope. ADR L0-002 scaffold items satisfied: Python 3.13 marker retained, direct runtime/test dependencies are declared, and the locked dependency graph is updated. |
| State | **Accepted** — parent diff/test review confirmed the bounded L0-002 change and WBS/ADR completion criteria. |
| Remaining work | None for L0-002. L0-003, L0-004, and L0-005 remain separate downstream tasks. |
| Next safe action | Begin one dependent task in a later cycle; do not continue automatically. |
| Unresolved | No new unresolved item introduced. Existing tracker unresolved items remain unchanged. |

## 10. I0-002 execution cycle (2026-09-05)

| Item | Result |
|---|---|
| Task ID | `I0-002` |
| Model / reasoning | `GPT-5 Codex` delegated implementation / high-equivalent; parent acceptance review / medium-high-equivalent |
| Selection rationale | Model policy classifies I0-002 as B3 integration/acceptance because provenance and timestamp semantics affect multiple downstream contracts. Implementation was delegated as one bounded change set and independently reviewed before acceptance. |
| Changed files | `analysis/app/orderscope_local/contracts/errors.py`, `analysis/app/orderscope_local/contracts/provenance.py`, `analysis/app/orderscope_local/contracts/provider.py`, `analysis/app/orderscope_local/contracts/__init__.py`, `analysis/tests/contracts/test_provenance_contract.py`, `analysis/tests/contracts/test_provider_contract.py`, and this Progress Tracker. Existing L0-002 changes were preserved and not modified in this cycle. |
| Tests / checks | Executor: contract tests **21 passed**, full suite **72 passed**, `git diff --check` clean. Parent: `UV_CACHE_DIR=/tmp/orderscope-parent-i0-002-uv-cache uv run pytest -q` — **72 passed**; `git diff --check` clean. |
| Completion criteria | WBS I0-002 criteria satisfied: canonical source reference, normalized-source SHA-256 hash, opaque provider revision, distinct event/published/filed/source-accepted timestamps, required retrieved/available/internal-accepted timestamps, UTC normalization, and `available_at <= retrieved_at <= accepted_at` are fixed by immutable types and tests. Unknown/date-only source times are not fabricated. |
| State | **Accepted** — parent review confirmed WBS completion, I0-001 dependency, existing I0-007 adapter-page integration, Proposed I0-005 provenance semantics, and secret/raw-body boundaries. |
| Remaining work | Downstream tasks remain separate cycles. |
| Next safe action | Continue according to the current snapshot above rather than this historical cycle entry. |
| Unresolved | No new unresolved item introduced. Existing provider/A0 and provisional-artifact acceptance questions remain unchanged. |

## 11. I0-003 execution cycle (2026-09-05)

| Item | Result |
|---|---|
| Task ID | `I0-003` |
| Model / reasoning | `gpt-5.6-terra` / medium implementation; parent Sol acceptance review |
| Selection rationale | Model policy assigns Terra with Sol review to the multi-file cursor/checkpoint contract. Scope was limited to one provider-neutral contract and its tests; no Provisional result was promoted. |
| Changed files | `analysis/app/orderscope_local/contracts/checkpoint.py`, `analysis/app/orderscope_local/contracts/__init__.py`, `analysis/tests/contracts/test_checkpoint_contract.py`, and this Progress Tracker. Pre-existing I0-002 and L0-002 changes were preserved. |
| Tests / checks | Executor: contract tests **33 passed**, full suite **84 passed**, `git diff --check` clean. Parent after invalid-record hardening: contract tests **34 passed**, full suite **85 passed**, `git diff --check` clean. |
| Completion criteria | WBS I0-003 criteria satisfied: checkpoints are scoped by provider and source; UTC half-open windows remain bounded across resume; opaque cursors, partial/error state, retry metadata, and observation time round-trip through a storage-neutral record; complete checkpoints cannot resume; provider raw error text/body and credentials are outside the durable schema. |
| State | **Accepted** — parent diff/test/semantic review confirmed I0-002 compatibility and the I0-007 bounded pagination/partial/error contract boundary. |
| Remaining work | I0-004 remains Ready. I0-005 remains Provisional; I0-006 and formal I0-007 acceptance remain gated by their documented dependencies. |
| Next safe action | Start `I0-004` as a separate cycle for stable IDs and duplicate/update/conflict classification. |
| Unresolved | No new unresolved item introduced. Existing provider/A0 and provisional-artifact acceptance questions remain unchanged. |

## 12. Progress-update rule

After normal implementation progress, update this file and do not mirror runtime state into the Critical Path or WBS. Update the Critical Path only when dependency structure, permanent gates, or safe-parallelization rules change.