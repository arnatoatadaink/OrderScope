# OrderScope — Current Critical Path Reconciliation

Status: **CURRENT DATE-INDEPENDENT OPERATING INDEX / MANAGEMENT INTEGRATED**
Updated: 2026-10-03
Scope: release management + canonical WBS / CP restart authority

## 1. Purpose

This file is the stable, date-independent entry point for selecting the current OrderScope restart point.

Detailed current CP authority is:

- `CURRENT_CRITICAL_PATH_RECONCILIATION_2026-10-03.md`

Companion authorities are:

- `CURRENT_UWBS_PROGRESS_TRACKER.md`
- `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
- `WBS_PROVISIONAL_ID_REGISTRY.md`
- `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
- `docs/release/V0_1_0_TO_V0_1_10_FINAL_TAG_LEDGER_2026-10-03.md`
- `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`

Historical dated CP documents and the integration pre-review remain evidence. They do not override the authorities above.

## 2. Management integration state

The management refresh branch was squash-merged into `main` on 2026-10-03.

```text
main integration commit:
f9dc1270db8d3b167a163edd8a0475747e2a404b
```

## 3. Accepted release state

```text
v0.1.0..v0.1.10  ACCEPTED / TAG READY
```

The exact cumulative targets remain frozen in the final tag ledger. `TAG READY` does not authorize tag creation or push.

## 4. Canonical namespace

```text
UWBS-101..104  FROZEN / CONFLICT / LEGACY-ONLY
UWBS-105       A0-018  Macro Release / Yen Carry Observability
UWBS-106       C0-001  Crypto registry + confirmed-transfer Fact
UWBS-107       C0-002  abnormal on-chain flow metrics/state
UWBS-108       C0-003  on-chain anomaly × market context
UWBS-109       C0-004  historical exploit / replay
```

## 5. Current release CP

### v0.1.11 — Crypto On-chain Event Intelligence

```text
REL-11A  C0-001 / UWBS-106  ACCEPTED / INTEGRATED
   -> REL-11B  C0-002 / UWBS-107  ACCEPTED / INTEGRATED
   -> REL-11C  C0-003 / UWBS-108  NEXT
   -> REL-11D  C0-004 / UWBS-109
   -> REL-11X  cumulative acceptance / TAG READY decision
```

Accepted crypto-market-structure evidence `UWBS-068..079` feeds C0-003 and C0-004. Abnormal transfer or market behavior alone must not be promoted to a confirmed security incident.

### v0.1.12 — Macro Release / Yen Carry Observability

```text
REL-12A  A0-018 macro release Fact / consensus / revision
   -> REL-12B  surprise + bounded event-window transmission
   -> REL-12C  CARRY_BUILD / CARRY_STABLE / CARRY_COOLING
   -> existing A0-005 carry-unwind / deleveraging interpretation
   -> REL-12D  historical / revision / stale-market / false-positive validation
   -> REL-12X  cumulative acceptance / TAG READY decision
```

## 6. Selected restart point

Current accepted v0.1.11 evidence:

```text
REL-11A / C0-001 / UWBS-106  ACCEPTED / INTEGRATED
REL-11B / C0-002 / UWBS-107  ACCEPTED / INTEGRATED
```

The selected feature restart is now:

```text
v0.1.11 REL-11C
  -> C0-003 / UWBS-108
```

After v0.1.11 acceptance, the planned next release begins at `v0.1.12 REL-12A / A0-018 / UWBS-105`.

## 7. Restart rule

After an interruption:

1. read this file;
2. read `CURRENT_CRITICAL_PATH_RECONCILIATION_2026-10-03.md` for detailed CP;
3. read `CURRENT_UWBS_PROGRESS_TRACKER.md` for task state;
4. use `WBS_PROVISIONAL_ID_REGISTRY.md` for identifier authority;
5. use the final tag ledger for v0.1.0..v0.1.10 boundaries;
6. never restart accepted UWBS-080..100 or PB-00..PB-10 work;
7. never start new work under frozen UWBS-101..104;
8. do not repeat REL-11A or REL-11B;
9. resume current feature work from `v0.1.11 REL-11C / C0-003 / UWBS-108` until evidence advances the CP.

No provider activation, Worker/Cron mutation, D1 mutation, paid procurement, live PB execution, automated trading, tag creation, history rewrite, or force push is authorized by this index.
