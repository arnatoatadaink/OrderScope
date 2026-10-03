# OrderScope — Current Critical Path Reconciliation

Status: **CURRENT DATE-INDEPENDENT OPERATING INDEX**
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

Historical dated CP documents remain evidence. They do not override the authorities above.

## 2. Accepted release state

```text
v0.1.0..v0.1.10  ACCEPTED / TAG READY
```

The exact v0.1.0..v0.1.10 cumulative targets are frozen in the final tag ledger.

`TAG READY` is evidence of release readiness only. This file does not authorize creation or push of Git tags.

The former PB-09/PB-10 pending state is historical. The reconstructed PB closeout boundary is accepted as `v0.1.10`.

Any future live-market execution is a new operational action and still requires fresh authorization.

## 3. Canonical namespace

```text
UWBS-101..104  FROZEN / CONFLICT / LEGACY-ONLY
UWBS-105       A0-018  Macro Release / Yen Carry Observability
UWBS-106       C0-001  Crypto registry + confirmed-transfer Fact
UWBS-107       C0-002  abnormal on-chain flow metrics/state
UWBS-108       C0-003  on-chain anomaly × market context
UWBS-109       C0-004  historical exploit / replay
```

Historical references to `UWBS-101..104` may be retained as provenance, but they must not be used as active implementation IDs. Context-insufficient historical references remain `AMBIGUOUS`.

## 4. Current release CP

### v0.1.11 — Crypto On-chain Event Intelligence

```text
REL-11A  C0-001 / UWBS-106
   -> REL-11B  C0-002 / UWBS-107
   -> REL-11C  C0-003 / UWBS-108
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

A0-018 extends the accepted macro/carry foundation; it does not duplicate `CARRY_UNWIND_CANDIDATE` or `DELEVERAGING_REGIME`.

## 5. Selected restart point

Management refresh MFR-01..06 is complete on the management branch. Current work is integration pre-review.

After integration review, the selected feature restart is:

```text
v0.1.11 REL-11A
  -> C0-001 / UWBS-106
```

After v0.1.11 acceptance, the planned next release begins at:

```text
v0.1.12 REL-12A
  -> A0-018 / UWBS-105
```

The release order is a planning decision; A0-018 has no technical dependency on C0-001..004.

## 6. Restart rule

After an interruption:

1. read this file;
2. read `CURRENT_CRITICAL_PATH_RECONCILIATION_2026-10-03.md` for detailed CP;
3. read `CURRENT_UWBS_PROGRESS_TRACKER.md` for task state;
4. use `WBS_PROVISIONAL_ID_REGISTRY.md` for identifier authority;
5. use the final tag ledger for v0.1.0..v0.1.10 boundaries;
6. use the v0.1.11/v0.1.12 release plan for planned release work;
7. never restart accepted UWBS-080..100 or PB-00..PB-10 work;
8. never start new work under frozen UWBS-101..104.

No provider activation, Worker/Cron mutation, D1 mutation, paid procurement, live PB execution, automated trading, tag creation, history rewrite, or force push is authorized by this index.
