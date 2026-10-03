# OrderScope — Management File Refresh Plan

Date: 2026-10-03
Status: Active planning report
Scope: WBS / CP / UWBS / version boundary / release readiness / current trackers / provisional-ID governance

## 1. Purpose

Refresh the repository's management files so that a reader can determine the current OrderScope state without accidentally treating dated evidence snapshots as current authority.

The refresh must preserve append-only historical evidence and update only the files that are intended to represent current state, canonical identifiers, active dependencies, or release boundaries.

## 2. Governing rule

Management files are classified into four roles.

| Class | Role | Mutation policy |
|---|---|---|
| A | Current-state authority | Keep synchronized with the latest accepted repository state |
| B | Identity / WBS authority | Update when provisional IDs, canonical mappings, or formal WBS incorporation changes |
| C | Release authority | Update when accepted version boundaries, TAG READY state, or release closeout changes |
| D | Evidence / historical snapshot | Preserve as immutable or append-only evidence; do not rewrite to mimic the current state |

A dated acceptance, audit, manifest, reconciliation, or post-integration report is evidence unless that document explicitly declares itself the current canonical authority.

## 3. Priority management files

### P0 — current-state and identity files

1. `docs/work-management/local-corporate-intelligence/CURRENT_CRITICAL_PATH_RECONCILIATION.md`
2. `docs/work-management/local-corporate-intelligence/CURRENT_UWBS_PROGRESS_TRACKER.md`
3. `docs/work-management/local-corporate-intelligence/CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
4. `docs/work-management/local-corporate-intelligence/WBS_PROVISIONAL_ID_REGISTRY.md`
5. `docs/release/V0_1_VERSION_BOUNDARY_PLAN_2026-09-28.md`
6. Final TAG READY / release ledger used for the v0.1.0-v0.1.10 boundary, if not yet incorporated into `main`

### P1 — formal WBS / CP incorporation targets

- Normative Analyst / Cross-Market WBS documents referenced by the provisional-ID registry
- Normative CP index / execution-order documents referenced by the current CP reconciliation
- Canonical WBS-unreflected backlog and active append files that still contain pending incorporation records

### P2 — evidence references used for reconciliation

- `REC_*` acceptance / manifest files
- `POST_*` integration review / audit files
- dated `*_RECONCILIATION_*` files
- accepted implementation reports and test evidence

P2 files are evidence inputs and should normally not be rewritten during this refresh.

## 4. Refresh sequence

The update order is dependency-driven.

```text
accepted evidence / integration state
        |
        v
release / TAG READY ledger
        |
        v
version boundary
        |
        +-------------------+
        |                   |
        v                   v
CURRENT CP            CURRENT UWBS
        |                   |
        +---------+---------+
                  v
      CURRENT overall progress tracker
                  |
                  v
      WBS provisional-ID / formal-WBS reconciliation
```

The provisional-ID registry can be updated earlier only when an ID collision blocks all downstream references. `UWBS-101` is currently such a blocker and must be resolved before new UWBS-101+ references are normalized.

## 5. Audit state model

Each management-file assertion is classified as:

- `CURRENT` — matches the latest accepted state.
- `STALE` — still describes a formerly valid state that has since advanced.
- `MISSING` — required current information is absent.
- `CONFLICT` — two active management sources assign incompatible meanings or states.

No file is modified solely because it is old; a dated file that is historical evidence can remain unchanged.

## 6. Planned work packages

### MFR-01 — UWBS namespace reconciliation

Goal: eliminate active provisional-ID ambiguity before updating trackers.

Tasks:

1. inventory all active references at and above `UWBS-101`;
2. compare branch chronology, merge status, and declared canonical status;
3. distinguish historical append evidence from current namespace ownership;
4. assign canonical IDs without rewriting historical evidence;
5. record explicit legacy-to-canonical aliases where required.

Acceptance condition: each active task has exactly one canonical provisional ID and historical references remain traceable.

### MFR-02 — release / TAG READY reconciliation

Goal: align the release boundary plan with the latest accepted tag-ready ledger and integration evidence.

Tasks:

1. verify the latest accepted v0.1.0-v0.1.10 boundary;
2. distinguish `TAG READY` from an actually created/pushed Git tag;
3. update stale reserved/pending states in the current release authority;
4. preserve prior release evidence as dated history.

Acceptance condition: the current release authority answers version readiness without requiring interpretation of obsolete snapshots.

### MFR-03 — CURRENT CP reconciliation

Goal: make `CURRENT_CRITICAL_PATH_RECONCILIATION.md` reflect the accepted feature path and any remaining market-dependent execution path.

Tasks:

1. reconcile PB closeout state;
2. reconcile accepted UWBS feature lanes;
3. incorporate newly formalized UWBS dependencies after MFR-01;
4. explicitly mark experimental/deferred stages that are not release blockers.

Acceptance condition: every open CP node has a clear predecessor, successor, blocker, and disposition.

### MFR-04 — CURRENT UWBS reconciliation

Goal: synchronize the current UWBS tracker with accepted implementation, integration, pending planning extensions, and canonical remaps.

Tasks:

1. verify accepted state through `UWBS-100`;
2. incorporate canonical post-100 planning tasks after MFR-01;
3. distinguish `Accepted`, `Integrated`, `Pending`, `Experimental`, and `Unreflected` states;
4. retain provenance links to dated acceptance/reconciliation evidence.

Acceptance condition: the tracker contains no active legacy aliases as if they were canonical IDs.

### MFR-05 — overall progress tracker reconciliation

Goal: make the aggregate tracker a summary of the reconciled release, CP, and UWBS authorities rather than an independent competing source of truth.

Tasks:

1. derive status from MFR-02 through MFR-04;
2. remove stale blocker statements already closed elsewhere;
3. retain unresolved external/provider/market-hours conditions explicitly.

Acceptance condition: the overall tracker has no state that contradicts the lower-level current authorities.

### MFR-06 — formal WBS / backlog incorporation review

Goal: close the gap between WBS-unreflected planning extensions and normative WBS/CP.

Tasks:

1. enumerate active `WBS_UNREFLECTED_*` files;
2. mark already incorporated records as incorporated rather than deleting historical files;
3. promote approved tasks into normative WBS/CP;
4. update `WBS_PROVISIONAL_ID_REGISTRY.md` with formal mappings when assigned.

Acceptance condition: every unreflected task is either pending with a reason, formally incorporated, superseded with an alias, or explicitly deferred.

## 7. Immediate known risk — UWBS-101 collision

Two incompatible uses of `UWBS-101` are known and must be resolved before MFR-03 through MFR-06:

1. Macro Release Surprise / Yen Carry Flow Observability, recorded on branch `docs/uwbs-101-macro-carry-observability` in a dated append created on 2026-10-01.
2. Crypto On-chain Security / cross-chain wallet-and-transfer Fact contract, recorded on `main` in a 2026-10-02 WBS-unreflected extension that reserves `UWBS-101..104`.

This plan does not decide the winner by date alone. Canonical ownership must be determined using repository state, merge/incorporation status, explicit canonical declarations, and the append-only registry rule. Historical text must not be rewritten even if one side is remapped.

## 8. Change discipline

- Do not alter accepted implementation code while reconciling management documentation unless a separate implementation defect is discovered.
- Do not erase historical UWBS aliases.
- Do not equate `TAG READY` with a pushed Git tag.
- Do not promote a planning extension into normative WBS/CP without recording the transition.
- Prefer additive canonical alias/remap records over history rewrites.
- After each management-file update, re-check all direct cross-references to the changed identifier or state.

## 9. Completion criteria

The management refresh is complete when:

1. no active provisional ID has more than one canonical task meaning;
2. current CP, current UWBS, overall tracker, release boundary, and ID registry agree;
3. all accepted v0.1.x boundaries are represented consistently;
4. historical evidence remains preserved and clearly separated from current authority;
5. WBS-unreflected extensions have explicit `Pending`, `Incorporated`, `Deferred`, or `Superseded/Remapped` disposition;
6. a fresh repository review can identify the next executable task without reconstructing state from multiple dated reports.

## 10. First execution step

Execute `MFR-01 — UWBS namespace reconciliation`, starting with the `UWBS-101` collision, before modifying the current UWBS/CP trackers.
