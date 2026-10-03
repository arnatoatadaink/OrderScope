# OrderScope — Management File Refresh Plan

Date: 2026-10-03
Status: **MFR-01..06 COMPLETE / INTEGRATION PRE-REVIEW**
Scope: WBS / CP / UWBS / version boundary / release readiness / current trackers / provisional-ID governance

## 1. Purpose

Refresh the repository's management files so that a reader can determine the current OrderScope state without accidentally treating dated evidence snapshots as current authority.

Historical evidence remains preserved. Current authorities are synchronized separately rather than rewriting older acceptance snapshots.

## 2. Governing rule

Management files use four roles:

| Class | Role | Mutation policy |
|---|---|---|
| A | Current-state authority | Keep synchronized with the latest accepted repository state |
| B | Identity / WBS authority | Update when canonical IDs or formal WBS mappings change |
| C | Release authority | Update when release boundaries or TAG READY state changes |
| D | Evidence / historical snapshot | Preserve as immutable or append-only historical evidence |

A dated historical report does not become current authority merely because it remains in the repository.

## 3. Current authorities after refresh

### Current / identity

- `CURRENT_CRITICAL_PATH_RECONCILIATION.md` — date-independent restart index
- `CURRENT_CRITICAL_PATH_RECONCILIATION_2026-10-03.md` — detailed current CP authority
- `CURRENT_UWBS_PROGRESS_TRACKER.md`
- `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
- `WBS_PROVISIONAL_ID_REGISTRY.md`
- `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`

### Release

- `docs/release/V0_1_0_TO_V0_1_10_FINAL_TAG_LEDGER_2026-10-03.md`
- `docs/release/V0_1_11_UWBS_NAMESPACE_CORRECTION_2026-10-03.md`
- `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`

### Formal post-100 WBS

- `docs/WORK_BREAKDOWN_CRYPTO_ONCHAIN_EVENT_INTELLIGENCE_2026-10-03.md`
- `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_POST100_2026-10-03.md`

### Historical release planning

- `docs/release/V0_1_VERSION_BOUNDARY_PLAN_2026-09-28.md` is historical/superseded for current release decisions.

## 4. Canonical post-100 result

```text
UWBS-101..104  FROZEN / CONFLICT / LEGACY-ONLY
UWBS-105       -> A0-018 -> v0.1.12
UWBS-106       -> C0-001 -> v0.1.11 REL-11A
UWBS-107       -> C0-002 -> v0.1.11 REL-11B
UWBS-108       -> C0-003 -> v0.1.11 REL-11C
UWBS-109       -> C0-004 -> v0.1.11 REL-11D
```

Current release sequence:

```text
v0.1.10  PB / active-market validation closeout  ACCEPTED / TAG READY
   -> v0.1.11  Crypto On-chain Event Intelligence
   -> v0.1.12  Macro Release / Yen Carry Observability
```

## 5. MFR completion ledger

| Work package | Result | Primary evidence |
|---|---|---|
| MFR-01 — namespace reconciliation | **COMPLETE** | `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md` |
| MFR-02 — release / TAG READY reconciliation | **COMPLETE** | final v0.1.0..10 tag ledger + v0.1.11/12 release authorities |
| MFR-03 — CURRENT CP reconciliation | **COMPLETE** | dated and date-independent CURRENT CP files |
| MFR-04 — CURRENT UWBS reconciliation | **COMPLETE** | `CURRENT_UWBS_PROGRESS_TRACKER.md` |
| MFR-05 — overall tracker reconciliation | **COMPLETE** | `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md` |
| MFR-06 — formal WBS / backlog incorporation | **COMPLETE** | A0-018, C0-001..004 formal WBS + canonical backlog append + MFR-06 closeout |

## 6. Historical namespace handling

The original collision used `UWBS-101` for both Macro/Carry and Crypto planning. The current resolution does not delete or rewrite that historical evidence.

Contextual mapping:

```text
Macro old UWBS-101 -> UWBS-105 -> A0-018
Crypto old UWBS-101 -> UWBS-106 -> C0-001
Crypto old UWBS-102 -> UWBS-107 -> C0-002
Crypto old UWBS-103 -> UWBS-108 -> C0-003
Crypto old UWBS-104 -> UWBS-109 -> C0-004
```

Context-insufficient old references remain `AMBIGUOUS`.

## 7. Release state

The exact cumulative boundaries for `v0.1.0..v0.1.10` are frozen in the final tag ledger and are `ACCEPTED / TAG READY`.

No Git tag creation or push has been authorized by the management refresh.

Planned release CP:

```text
v0.1.11
REL-11A -> REL-11B -> REL-11C -> REL-11D -> REL-11X

v0.1.12
REL-12A -> REL-12B -> REL-12C -> existing A0-005 -> REL-12D -> REL-12X
```

## 8. Integration pre-review

Current phase: **integration pre-review**.

The review must verify:

1. all CURRENT files point to the same restart state;
2. no active source treats UWBS-101..104 as canonical implementation IDs;
3. WBS registry records the formal A0-018 / C0-001..004 mappings;
4. release documents agree that v0.1.11 = C0-001..004 and v0.1.12 = A0-018;
5. old release-planning documents are explicitly historical/superseded where their states conflict with current authorities;
6. accepted v0.1.0..10 targets remain unchanged;
7. no tag creation, live-provider activation, Worker/Cron mutation, D1 mutation, PB execution, history rewrite, or force push was introduced by documentation reconciliation.

## 9. Selected next action

```text
CURRENT: integration pre-review / authority-drift check
NEXT after review: merge-readiness decision for the management branch
NEXT feature after integration: v0.1.11 REL-11A / C0-001 / UWBS-106
```

`v0.1.12 REL-12A / A0-018 / UWBS-105` follows the planned release order after v0.1.11 acceptance. A0-018 is not technically dependent on C0-001..004; the ordering is release governance.

## 10. Change discipline

- Preserve historical evidence and aliases.
- Current planning uses canonical IDs only.
- Do not equate `TAG READY` with a created/pushed Git tag.
- Do not alter accepted implementation code as part of management reconciliation.
- Do not authorize provider/runtime/trading actions through a management document.

The management refresh work packages are closed; remaining work is review of authority consistency and merge readiness.
