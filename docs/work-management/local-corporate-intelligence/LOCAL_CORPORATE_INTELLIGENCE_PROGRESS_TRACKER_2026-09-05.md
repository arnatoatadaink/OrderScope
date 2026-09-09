# OrderScope — Local Corporate Intelligence Progress Tracker

Status: active operational tracker (non-normative)
Date: 2026-09-09
Parent WBS: `../../WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Integrated CP: `../../WORK_PLAN_LOCAL_CORPORATE_INTELLIGENCE_CRITICAL_PATH_2026-09-05.md`
Extension WBS: `../../WORK_BREAKDOWN_ANALYST_CROSS_MARKET_2026-09-05.md`
Model assignment: `MODEL_ASSIGNMENT_POLICY_2026-09-05.md`
Runtime-status authority: **this file**

## 1. Purpose and authority

This file is the sole integrated authority for Local Corporate Intelligence runtime progress. Track current status, accepted/provisional/ready/blocked state, restart point, execution evidence, unresolved items, and next safe action here.

The Parent WBS defines completion conditions. The Integrated Critical Path defines static dependency structure, permanent gates, and safe parallelization. Neither should be changed merely because runtime progress advanced.

This tracker was fully reconciled on 2026-09-09 after the E0, O0, N0, and N1 implementation cycles had advanced beyond the older 2026-09-08 snapshot. Detailed historical per-task evidence remains available in Git history and task handoff files; this file intentionally prioritizes the current integrated runtime state.

## 2. Status vocabulary

| Status | Meaning |
|---|---|
| Accepted | WBS completion conditions and dependencies are satisfied; safe as a downstream prerequisite |
| In progress | Currently being implemented or reconciled |
| Provisional result | Artifact exists, but an upstream dependency or formal acceptance is pending |
| Ready | Dependencies are satisfied; safe to start |
| Blocked | Waiting on an external window, unresolved contract, or upstream result |
| Not started | Dependency gate is closed or work has not started |

## 3. Current integrated snapshot

### 3.1 Common contracts / SEC / Earnings / Official / News

| Lane / task | Status | Evidence / interpretation | Next action |
|---|---|---|---|
| I0-001..007 | Accepted | Common registry, provenance, checkpoint, identity, Fact Store, temporary-content, and common adapter-test contracts were accepted before downstream adapter work | Reference only |
| S0-001..007 | Accepted | SEC conditions, submissions, FilingRecord, target forms, document acquisition, Company Facts/XBRL, and Canary acceptance are complete at the v0.1 fixture/controlled-live boundary | Reference only |
| E0-001..007 | Accepted | Earnings contract, SEC detection, IR fallback, basic Facts, segment fallback, segment identity, and AMD/NVDA quality report are accepted | Reference only; E0-007 is a downstream prerequisite |
| O0-001..005 | Accepted | Official source registry, feed acquisition, statement/implementation semantics, relevance, and quality acceptance are complete | Reference only; O0-005 is a downstream prerequisite |
| N0-001..004 | Accepted | Provider decision, metadata adapter, canonicalization, and temporary body access are accepted | Reference only |
| N1-001..005 | Accepted | Event taxonomy, deterministic extraction, body extraction, contradiction/review, and retention controller are accepted | News gate for X0-001 is satisfied |
| N1-006 | Ready* | Dependency N1-005 and E0-007 are Accepted; execution still needs a 1–3 month News-vs-SEC/IR comparison dataset/reference window | Run when evaluation data is available; does not replace the Local-foundation gate |

`*` Ready means dependency-ready. Dataset availability still determines whether the evaluation can produce meaningful recall/lag/misattribution results in the current cycle.

### 3.2 Local foundation / market import and quality

| Task | Status | Evidence / interpretation | Next action |
|---|---|---|---|
| L0-001 | Accepted / inherited prerequisite | L0-002 was accepted under the existing local-stack ADR dependency; no new runtime issue was found in this reconciliation | Reference only |
| L0-002 | Accepted | Scaffold and Git boundary were accepted; `analysis/config` currently contains only its scaffold README | Reference only |
| L0-003 | Ready | Depends on L0-002; current branch has no implemented config/secret module under `orderscope_local` | **Primary next implementation candidate** |
| L0-004 | Ready | Depends on L0-002; current branch has no localhost health/API foundation under `orderscope_local` | Can run after overlap review, parallel to L0-003/L0-005 if files stay disjoint |
| L0-005 | Ready | Depends on L0-002; current branch has no local migration/catalog implementation under `orderscope_local` | **Critical prerequisite for L1-001** |
| L0-006 | Not started | Depends on L0-003, L0-004, and L0-005 | Start only after those three are Accepted |
| L1-001 | Not started | Depends on L0-005 | Start after L0-005 acceptance |
| L1-002 | Not started | Depends on L1-001 | Start after manifest contract |
| L1-003 | Blocked | Real D1 export requires separately approved `SMOKE-007` change window | Keep independent from fixture path |
| L1-004 | Not started | Fixture path depends on L1-002; real-data completion additionally requires L1-003 | Build fixture dataset path first after L1-002 |
| L1-005 | Not started | Depends on L1-004 | **Remaining unsatisfied X0-001 gate** |
| L1-006 | Not started | Depends on L0-004 and L1-005 | Later read-only import/dataset API work |

Repository reconciliation on 2026-09-09 found only the domain packages `contracts`, `sec`, `earnings`, `official`, and `news` under `analysis/app/orderscope_local`; there is no local config/health/migration/import/market-quality package yet. Therefore L1-005 must not be treated as implemented or provisional merely because the Corporate Intelligence source lanes are complete.

## 4. X0 gate reconciliation

### X0-001 — unified timeline

Static WBS dependencies:

```text
L1-005 + I0-005 + E0-007 + N1-005 + O0-005
```

Runtime state after this reconciliation:

```text
I0-005  Accepted
E0-007  Accepted
N1-005  Accepted
O0-005  Accepted
L1-005  NOT STARTED
```

Therefore:

```text
X0-001 = Blocked by L1-005 only
```

Do **not** begin X0-001 yet. The shortest remaining path is:

```text
L0-005
  -> L1-001
  -> L1-002
  -> L1-004 fixture path
  -> L1-005
  -> X0-001
```

`L1-003` remains an independent remote-real-data gate. It is required when promoting the market dataset path from fixture acceptance to real D1 data, but it should not block development of L1-001/002 and the fixture form of L1-004/005.

### Other X0 tasks

| Task | Runtime status | Reason |
|---|---|---|
| X0-001 | Blocked | L1-005 not started |
| X0-002 | Not started | Coverage summary should wait until remaining Local/market adapter path exists and adapter states are reconciled |
| X0-003 | Not started | Depends on L0-004 plus X0-001/002 |
| X0-004 | Not started | Depends on adapter availability and L0-006 |
| X0-005 | Not started | Depends on X0-001..004 |
| X0-006 | Not started | Depends on X0-005 |

## 5. Parallel lanes

### Lane A — Corporate information core

`I0`, `S0`, `E0`, `O0`, and News through `N1-005` are Accepted. The next source-quality task is `N1-006`, but it is an evaluation task and is not the remaining serial blocker for X0-001.

### Lane B — Local foundation / market quality

This is now the **primary serial lane** for the Local Intelligence MVP.

Recommended order:

1. `L0-005` — migration foundation, because it opens L1-001.
2. `L0-003` and `L0-004` — can be implemented as separate bounded cycles after overlap review; both are also required before L0-006.
3. `L1-001` → `L1-002` → fixture `L1-004` → `L1-005`.
4. `L1-003` stays blocked until the approved remote D1/SMOKE-007 window; reconcile real data later without invalidating fixture progress.

### Lane C — Cross-Market extension

| Task | Status | Next action |
|---|---|---|
| A0-001 | Provisional result | Implementation integration can proceed in a separate Cross-Market cycle if desired |
| A0-002 | Not started | Dataset/source definition may proceed independently; not a serial Core blocker unless release DoD changes |

## 6. Current model / Agent assignment

| Role / task | Assignment | Reasoning | Note |
|---|---|---|---|
| Orchestrator | Sol | medium | Reconcile tracker/WBS/CP/repository evidence and select one bounded next task |
| Primary next serial task | Luna/Terra + Sol review | medium | `L0-005` is bounded local migration foundation but affects downstream persistence/import work |
| L0-003 / L0-004 | Luna/Terra | per Model Assignment Policy | Safe bounded Local-foundation work after overlap review |
| N1-006 evaluation | Terra + Sol review | medium/high | Dataset quality, matching methodology, lag, and ticker-misattribution measurement need careful review |
| A0-002 dataset/source definition | Terra | medium | Separate validation lane |

Record the actual model/reasoning and acceptance evidence in the handoff or tracker update for each future cycle.

## 7. Known non-blockers / deferred items

- `L1-003` remote D1 export change window remains deferred and does not block fixture-path implementation through L1-005.
- `N1-006` is important for News quality/M4 acceptance but is not the current serial dependency of X0-001.
- `A0-002` remains a validation lane and is not currently a serial blocker for Core Corporate Intelligence.
- Worker remains Shadow; Local work must not directly change Worker runtime state.

## 8. Current restart rule

- **Main local session:** start `L0-005` as the primary serial task toward L1-005/X0-001.
- **Second bounded local session:** `L0-003` or `L0-004` may proceed after task/file-overlap review.
- **News evaluation session:** start `N1-006` only when a credible 1–3 month News and SEC/IR comparison dataset/reference window is available.
- **Cross-Market session:** A0 work remains separate.
- Do not start X0-001 until L1-005 is Accepted.
- Do not conflate fixture completion with the separately gated real D1 export/change window.

## 9. Unresolved items

- `SMOKE-007` / L1-003 approved remote D1 export change window and real-data completion evidence.
- N1-006 exact 1–3 month evaluation window and available provider News history for the chosen account/plan.
- Analyst Consensus as-of history provider and contract conditions.
- AI/Semiconductor proxy definition for A0-002.
- short/borrow data provider for H4 validation.
- whether A0-002 becomes mandatory for v0.1 release acceptance.

Do not infer unresolved values. Update this tracker only from repository evidence, local test evidence supplied by the user, controlled-run evidence, or confirmed external contract/source information.

## 10. 2026-09-09 reconciliation evidence

| Item | Result |
|---|---|
| Trigger | User requested re-synchronization after N1-005 local acceptance |
| N1-005 local acceptance | focused **11 passed**; full suite **345 passed**; `git diff --check` clean |
| E0 evidence | `E0-007_WEB_IMPLEMENTATION_HANDOFF_2026-09-09.md` is Accepted; E0-001..006 were already accepted prerequisites |
| O0 evidence | `O0-005_WEB_IMPLEMENTATION_HANDOFF_2026-09-09.md` is Accepted; O0-001..004 were already accepted prerequisites |
| News evidence | N0-001..004 and N1-001..005 handoffs/implementation cycles are accepted; N1-005 acceptance recorded in its handoff |
| Repository shape | `analysis/app/orderscope_local` contains `contracts`, `sec`, `earnings`, `official`, and `news`; no local foundation/import/market-quality implementation package exists yet |
| Config shape | `analysis/config` contains only scaffold `README.md` |
| X0 decision | X0-001 remains blocked solely by L1-005 among its explicit dependencies |
| Primary next task | `L0-005` |
| Critical Path/WBS update | **None** — dependency structure and completion definitions did not change; only runtime state was reconciled |

## 11. Historical accepted evidence index

The previous tracker revision contained detailed execution-cycle tables for L0-002, I0-002..007, and S0-001..007. Those records remain available in Git history. Later E0/O0/N0/N1 details are stored in their task-specific Web Implementation Handoffs under this directory.

Current downstream code must rely on the Accepted states in the integrated snapshot above rather than stale historical "next action" text from older revisions.

## 12. Progress-update rule

After normal implementation progress, update this file and do not mirror runtime state into the Critical Path or WBS. Update the Critical Path only when dependency structure, permanent gates, or safe-parallelization rules change.