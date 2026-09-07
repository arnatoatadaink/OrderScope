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
| I0-004 | Accepted | Stable filing/article/signal identities and immutable new/duplicate/update/conflict classification are fixed by contract tests; parent diff/test/semantic review completed in the 2026-09-06 execution cycle | Reference when connecting I0-007 and downstream adapters |
| I0-005 | Accepted | Immutable Fact Store contracts and fixtures separate Fact, Evidence, Relationship, DerivedMetric, and Interpretation while using I0-002 provenance; parent semantic/diff/test review completed in the 2026-09-06 execution cycle | Reference when implementing I0-006 and reconciling downstream provisional artifacts |
| I0-006 | Accepted | Immutable temporary-content lifecycle types, expiry/deletion/exception invariants, and contract tests were reviewed and accepted in the 2026-09-06 execution cycle | Reference when connecting I0-007 and downstream content adapters |
| I0-007 | Accepted | The common contract-test kit connects the accepted checkpoint, stable-identity, and temporary-content contracts; parent semantic/diff/test review completed in the 2026-09-06 execution cycle | Reference when implementing provider adapters |
| S0-001 | Accepted | The WEB-005 handoff was reconciled against the W0-004 checklist and current SEC primary sources; parent evidence and semantic review completed in the 2026-09-08 execution cycle | Reference when implementing SEC adapters and recheck before live deployment or after policy changes |
| S0-002 | Accepted | The bounded AMD/NVDA Submissions adapter, recent/history fixtures, common-contract integration, and parent semantic/test review completed in the 2026-09-08 execution cycle | Reference when implementing FilingRecord persistence |
| S0-003 | Ready | Depends on Accepted `S0-002` | Implement FilingRecord persistence in a separate cycle |
| S0-004 | Provisional result | Form-filter implementation/report exists but is not yet connected to S0-003 | Confirm integration after S0-003 and preserve acceptance evidence |
| S0-005 | Not started | Depends on `S0-003` + `I0-006` | Implement temporary filing-document content handling |
| S0-006 | Not started | Depends on `S0-003` | Implement the Company Facts/XBRL adapter |
| S0-007 | Provisional result | Early validation evidence may exist; WBS acceptance testing follows S0-004..006 integration | Run formal Canary acceptance after integration |
| E0-001..007 | Not started | Depends on the S0 lane and I0-005 | Start sequentially after S0-007 |
| N1 / O0 / X0 | Not started | Depends on the Core Fact/SEC/Earnings lanes | Start later on the Core CP |

## 4. Parallel lanes

### Lane A — Core contracts

Latest accepted task: `I0-007`. The Core contract lane is complete; select the next task only in a separate cycle after checking its remaining gates.

Static dependency order is defined in the Critical Path; this section records only the current runtime position.

### Lane B — Local foundation

`L0-002` is Accepted. Next safe dependent work is one of `L0-003`, `L0-004`, or `L0-005`, subject to task/file-overlap review.

`L1-003` remains blocked by the separately approved `SMOKE-007` change window and does not block fixture work.

### Lane C — Cross-Market extension

| Task | Status | Next action |
|---|---|---|
| A0-001 | Provisional result | Design complete and its I0-002/I0-005 implementation-acceptance dependencies are satisfied | Reflect fields/schema/fixtures in a separate Cross-Market cycle |
| A0-002 | Not started | Dataset/source definition may proceed before final schema write |

### Lane D — SEC / Earnings

S0-002 is Accepted. S0-003 is Ready; do not start its persistence work in the S0-002 cycle.

## 5. Current model / Agent assignment

| Role / task | Assignment | Reasoning | Note |
|---|---|---|---|
| Orchestrator | Sol | medium | Select and review one task against the Tracker, WBS, Critical Path, and repository evidence |
| S0-003 implementation | Terra | medium | FilingRecord persistence is a multi-file provider-neutral integration task |
| Local-foundation bounded work | Luna/Terra | per Model Assignment Policy | Select one Ready task only |
| A0-002 dataset/source definition | Terra | medium | No final schema write or hypothesis integration yet |

Record the actual model, reasoning effort, delegation rationale, and review result at the end of each cycle.

## 6. Known non-blockers / deferred items

- `L1-003` remote D1 export change window is deferred and does not block local fixture work.
- `A0-002` is a validation lane and is not currently a serial blocker for Core Corporate Intelligence.
- Preserve and reconcile provisional artifacts for `I0-007` and `S0-004`; do not discard them.

## 7. Current restart rule

- Main local session: start `S0-003` in a separate cycle; `S0-002` is Accepted
- Second parallel local session: choose one Ready Local-foundation task (`L0-003`, `L0-004`, or `L0-005`) after overlap review
- Cross-Market session: A0-001 implementation integration or `A0-002` dataset/source definition, with one task selected per cycle
- SEC implementation may continue with `S0-003`; do not automatically continue to its downstream tasks

## 8. Unresolved items

- Analyst Consensus as-of history provider and contract conditions
- AI/Semiconductor proxy definition for A0-002
- short/borrow data provider for H4 validation
- whether A0-002 becomes mandatory for v0.1 release acceptance
- exact evidence needed to promote provisional `S0-004/S0-007` artifacts after dependency integration

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

## 12. I0-004 execution cycle (2026-09-06)

| Item | Result |
|---|---|
| Task ID | `I0-004` |
| Model / reasoning | `gpt-5.6-terra` / high implementation; parent Sol-equivalent acceptance review / medium-high |
| Selection rationale | The Model Assignment Policy classifies stable identity and update/duplicate/conflict semantics as a high-reasoning Terra implementation with Sol acceptance review because the boundary affects I0-007 and multiple downstream adapters. The implementation remained one bounded contract-and-test change set. |
| Changed files | `analysis/app/orderscope_local/contracts/identity.py`, `analysis/app/orderscope_local/contracts/__init__.py`, `analysis/tests/contracts/test_identity_contract.py`, and this Progress Tracker. Existing accepted and provisional artifacts were preserved. |
| Tests / checks | Executor: focused tests **19 passed**, full suite **104 passed**, `git diff --check` clean. Parent: `UV_CACHE_DIR=/tmp/orderscope-parent-i0-004-final uv run pytest -q analysis/tests/contracts/test_identity_contract.py` — **19 passed**; full suite — **104 passed**; `git diff --check` clean. |
| Completion criteria | WBS I0-004 criteria satisfied: SEC accession identities are global; article and signal identities are provider-scoped; all are validated immutable values paired with the accepted I0-002 SHA-256 `ContentHash`. Distinct identity is `new`; same identity/hash is `duplicate`; same identity/different hash is `update` only with an explicit matching predecessor-to-successor relationship and otherwise is `conflict`. Tests reject ambiguous, reversed, cross-scope, secret-like, and invalid identity inputs; the durable record shape contains no raw-content or credential field. |
| State | **Accepted** — parent diff/test/semantic review confirmed the I0-002 dependency, append-only I0-005 supersession compatibility, I0-007 secret boundary, SEC amendment-as-distinct-accession behavior, and no provider payload or credential fields. |
| Remaining work | I0-005 remains Provisional and must be reconciled and formally accepted in a separate cycle. I0-006 and formal I0-007 acceptance remain gated by their documented dependencies. |
| Next safe action | Start `I0-005` reconciliation and formal acceptance as a separate cycle; do not continue automatically. |
| Unresolved | No new unresolved item introduced. Storage integration must select the accepted predecessor explicitly and must not reinterpret a hash mismatch as an update without a revision relationship. |

## 13. I0-005 execution cycle (2026-09-06)

| Item | Result |
|---|---|
| Task ID | `I0-005` |
| Model / reasoning | Parent GPT-5 Codex / high-equivalent implementation and acceptance review |
| Selection rationale | The Model Assignment Policy classifies I0-005 as B3 `Terra high + Sol review`. Session rules did not permit unsolicited sub-Agent delegation, so the parent preserved those as separate implementation and semantic-review responsibilities while completing one bounded change set. |
| Changed files | `analysis/app/orderscope_local/contracts/fact_store.py`, `analysis/app/orderscope_local/contracts/__init__.py`, `analysis/tests/contracts/test_fact_store_contract.py`, `docs/ADR_FACT_STORE_LOGICAL_SCHEMA_v0.1.md`, and this Progress Tracker. Pre-existing accepted I0-004 working-tree changes were preserved. |
| Tests / checks | Focused Fact Store contract tests — **8 passed** after hardening; full suite — **112 passed**; `python3 -m compileall -q analysis/app analysis/tests` passed; `git diff --check` clean. |
| Completion criteria | WBS I0-005 criteria satisfied: immutable Fact, Evidence, Relationship, DerivedMetric, and Interpretation types remain distinct historical records. Fixtures cover a filing Fact with reciprocal Evidence, amendment history, a corporate Relationship, a two-input DerivedMetric, an Interpretation with explicit basis, contradicting Evidence, secret/raw-body exclusion, and availability-aware as-of history. Source-grounded records use the accepted I0-002 Provenance types and timestamp order. |
| State | **Accepted** — parent diff/test/semantic review confirmed the I0-002 dependency, I0-004 external-identity boundary, append-only supersession, downstream A0/E0/N1/O0 compatibility, and the deferral of physical persistence and temporary-content lifecycle details to L0-005/I0-006. |
| Remaining work | I0-006 is Ready. I0-007 remains Provisional until I0-006 is Accepted and its accepted I0-003/I0-004 contracts are connected. A0-001 implementation integration is now dependency-ready but remains a separate lane and cycle. |
| Next safe action | Start `I0-006` as a separate main cycle; do not automatically continue to I0-007 or a parallel lane. |
| Unresolved | No provider or contract semantics were inferred. Physical migration layout remains L0-005 scope; temporary content expiry/delete-proof/exception details remain I0-006 scope. |

## 14. I0-006 execution cycle (2026-09-06)

| Item | Result |
|---|---|
| Task ID | `I0-006` |
| Model / reasoning | Terra-equivalent implementation / medium; Sol-equivalent parent acceptance review / medium |
| Selection rationale | The Model Assignment Policy assigns Terra + Sol to the multi-file temporary-content lifecycle contract because retention, expiry, deletion proof, and exception semantics extend the Accepted I0-005 boundary. The work remained one bounded contract/schema/test change set; no downstream adapter or provisional result was promoted. |
| Changed files | `analysis/app/orderscope_local/contracts/temporary_content.py`, `analysis/app/orderscope_local/contracts/__init__.py`, `analysis/tests/contracts/test_temporary_content_contract.py`, `docs/ADR_TEMPORARY_CONTENT_LIFECYCLE_v0.1.md`, and this Progress Tracker. Existing accepted/provisional artifacts were preserved. |
| Tests / checks | Focused lifecycle tests **6 passed**; full suite **118 passed**; `python3 -m compileall -q analysis/app analysis/tests` passed; `git diff --check` clean. Initial uv cache permission issue was avoided with `UV_CACHE_DIR=/tmp/orderscope-i0-006-uv-cache`; no repository or source issue was found. |
| Completion criteria | WBS I0-006 criteria satisfied: immutable content reference, `temporary_success` / `temporary_exception` retention classes, UTC capture/expiry fields, deletion proof, exception reason, secret/body exclusion, state/class alignment, and a 30-day maximum for exception content are fixed by types, ADR, and tests. Physical persistence and retention-worker behavior remain downstream. |
| State | **Accepted** — parent diff/test/semantic review confirmed I0-005 compatibility, the successful-body deletion handoff, exception expiry, deletion audit, and no raw body or credential fields. |
| Remaining work | I0-007 remains Provisional until I0-003, I0-004, and I0-006 are connected and formally accepted. Downstream SEC/content adapters remain gated by I0-007. |
| Next safe action | Start I0-007 reconciliation and formal acceptance as a separate cycle; do not automatically continue to SEC or parallel lanes. |
| Unresolved | No new unresolved item introduced. The exact physical retention worker, storage layout, and provider-specific body-access behavior remain downstream task scope. |

## 15. I0-007 execution cycle (2026-09-06)

| Item | Result |
|---|---|
| Task ID | `I0-007` |
| Model / reasoning | GPT-5 Codex delegated implementation / Terra-high responsibility; parent Sol-equivalent acceptance review / medium |
| Selection rationale | The Model Assignment Policy classifies I0-007 as B3 `L/T+S` with high implementation reasoning because it promotes a provisional cross-contract test kit after integrating three accepted upstream contracts. One bounded implementation change set was delegated, then independently reviewed by the parent. |
| Changed files | `analysis/app/orderscope_local/contracts/provider.py`, `analysis/app/orderscope_local/contracts/__init__.py`, `analysis/tests/contracts/test_provider_contract.py`, and this Progress Tracker. WBS and Critical Path were unchanged because no completion condition or dependency structure changed. |
| Tests / checks | Executor: focused upstream/common contract tests **52 passed**, full suite **124 passed**, compileall passed, and `git diff --check` clean. Parent: focused provider tests **14 passed** during review; final full suite **124 passed**; `python3 -m compileall -q analysis/app analysis/tests` passed; `git diff --check` clean. |
| Completion criteria | WBS I0-007 criteria satisfied: the common kit validates UTC availability/retrieval timestamp order, bounded cursor pagination, safe partial/error replay, bounded retry metadata, stable new/duplicate/update/conflict classification, optional temporary-content lifecycle handoff, and recursive credential/provider-body non-exposure. It delegates durable state and identity semantics to the accepted I0-003/I0-004 contracts and validates I0-006 content metadata without fabricating downstream acceptance timestamps. |
| State | **Accepted** — all I0-003/I0-004/I0-006 dependency gates are Accepted, and parent diff/test/semantic review confirmed compatibility with legacy normalized mappings and downstream adapter use. |
| Remaining work | No I0-007 work remains. S0-002 is no longer gated by I0-007, but S0-001 still requires local acceptance from the existing Web handoff before SEC adapter implementation starts. |
| Next safe action | Reconcile and formally accept S0-001 in a separate cycle; do not automatically begin S0-002 or another lane. |
| Unresolved | Provider-specific schemas and operational error messages remain outside durable Core contracts. Physical retention workers and provider-specific body access remain downstream scope. Existing provider/A0 unresolved items remain unchanged. |

## 16. S0-001 execution cycle (2026-09-08)

| Item | Result |
|---|---|
| Task ID | `S0-001` |
| Model / reasoning | Terra-equivalent bounded official-source research / medium; parent Sol-equivalent acceptance review / medium |
| Selection rationale | The Model Assignment Policy assigns S0-001 to Terra research plus Sol review. The cycle reconciled the existing WEB-005 handoff against the W0-004/WEB-003 checklist and current SEC primary sources without starting adapter implementation. |
| Changed files | This Progress Tracker only. WBS and Critical Path were unchanged because no completion condition, dependency structure, permanent gate, or safe-parallelization rule changed. |
| Evidence / checks | Rechecked SEC Developer Resources, Webmaster FAQ, EDGAR Data APIs, Accessing EDGAR Data, and Privacy Information on 2026-09-08. Official conditions remain: a declared organization/contact User-Agent; an aggregate maximum of 10 requests/second regardless of machine count; efficient/bounded access and a 10-minute below-threshold recovery condition; no authentication or API key for the public Submissions/XBRL data APIs; no CORS support on `data.sec.gov`; documented Submissions, XBRL, bulk, index, and Archives routes; reusable public EDGAR filing content with third-party artwork/logo/trademark exceptions; and no explicit public-filing local-retention limit, whose absence is not treated as permission. Parent review independently checked the official sources and `git diff --check`. |
| Completion criteria | WBS S0-001 criteria satisfied: current official User-Agent, fair-access/rate rules, endpoints, and storage/reuse conditions are recorded using the W0-004 checklist. The 2026-09-08 refresh found no material change from WEB-005. |
| State | **Accepted** — parent review confirmed the W0-004 dependency, current official evidence, public-data-versus-EDGAR-Next authentication boundary, CORS constraint, and separation of SEC reuse permission from OrderScope retention policy. |
| Remaining work | No S0-001 work remains. Rate limiting, User-Agent configuration, backoff/cooldown behavior, controlled live checks, and temporary-content persistence are downstream S0-002/S0-005/S0-007 implementation and test scope. |
| Next safe action | Start S0-002 as a separate cycle; do not automatically begin another SEC task. |
| Unresolved | SEC publishes no formal User-Agent grammar, exact block HTTP status/header behavior is not guaranteed, and no explicit local-retention duration was found. Recheck official conditions before live deployment and when SEC pages or policy change. |

## 17. S0-002 execution cycle (2026-09-08)

| Item | Result |
|---|---|
| Task ID | `S0-002` |
| Model / reasoning | Parent GPT-5 Codex / Terra-medium-equivalent implementation and Sol-equivalent acceptance review / medium |
| Selection rationale | The Model Assignment Policy classifies S0-002 as a bounded multi-file provider adapter for Terra/medium. Session rules did not permit unsolicited sub-Agent delegation, so the parent preserved implementation and acceptance-review responsibilities while completing one bounded S0-002 change set. |
| Changed files | `analysis/app/orderscope_local/sec/submissions.py`, `analysis/app/orderscope_local/sec/__init__.py`, `analysis/tests/sec/test_submissions.py`, and this Progress Tracker. WBS and Critical Path were unchanged because no completion condition or dependency structure changed. |
| Tests / checks | Focused Submissions adapter tests **9 passed** after acceptance hardening; the full suite **133 passed**. `python3 -m compileall -q analysis/app analysis/tests` passed and `git diff --check` was clean. Remote comparison after `git fetch origin --prune` confirmed the starting branch was **0 ahead / 0 behind** its upstream. |
| Completion criteria | WBS S0-002 criteria satisfied: the adapter accepts only the fixed AMD/NVDA canary sources, reads current and intersecting historical Submissions files inside a UTC half-open window, paginates with an opaque cursor, and emits provider-neutral accession identities plus bounded filing metadata. SEC columnar JSON and transport exception bodies do not cross the adapter boundary. Tests cover declared contact-bearing User-Agent configuration, a shareable fixed-interval limiter capped at the SEC public ceiling, history-window selection, cursor resume, malformed provider responses, retryable sanitized failures, CIK/history-file cross-company rejection, and common page/checkpoint contracts. |
| State | **Accepted** — both upstream gates were Accepted, and parent diff/test/semantic review confirmed I0-003/I0-004/I0-007 compatibility, stable accession identity, deterministic content hashing, bounded AMD/NVDA scope, and no credential or raw-provider-body fields. |
| Remaining work | S0-003 FilingRecord persistence remains a separate task. Production HTTP transport wiring, deployment-level shared-limiter configuration, operational cooldown behavior, and controlled live fetching remain downstream local-foundation/S0-007 integration scope; S0-004 and S0-007 provisional artifacts were preserved. |
| Next safe action | Start `S0-003` in a separate cycle and connect these normalized adapter items to idempotent FilingRecord persistence; do not automatically continue to S0-004/S0-005/S0-006. |
| Unresolved | The exact SEC block status/header behavior remains provider-dependent and must not be inferred. Offset cursors are stable for the adapter's deterministic oldest-first snapshot ordering, while persistence must still deduplicate by accession when a later provider snapshot changes. Existing tracker unresolved items remain unchanged. |

## 18. Progress-update rule

After normal implementation progress, update this file and do not mirror runtime state into the Critical Path or WBS. Update the Critical Path only when dependency structure, permanent gates, or safe-parallelization rules change.
