# OrderScope — Current UWBS Progress Tracker

Status: **CURRENT UWBS OVERLAY**
Updated: 2026-10-03

This tracker is the current UWBS-specific overlay for canonical task progress. It supplements historical acceptance records and older integrated trackers.

Canonical ID meanings are governed by `WBS_PROVISIONAL_ID_REGISTRY.md`.
Namespace collision handling is governed by `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`.
Release boundaries through `v0.1.10` are governed by `docs/release/V0_1_0_TO_V0_1_10_FINAL_TAG_LEDGER_2026-10-03.md`.
Planned release work for `v0.1.11` and `v0.1.12` is governed by `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`.

## 1. Status rule

A UWBS item is not downgraded merely because its original branch is old or diverged. Use the newest accepted evidence in this order:

1. accepted task/local-validation evidence;
2. reconciliation / selective-replay evidence;
3. cumulative release acceptance / tag-ready evidence;
4. current namespace, formal WBS and release authority.

Historical evidence remains immutable. Current planning references must use canonical IDs.

## 2. Accepted / integrated ranges

| UWBS range | Current status | Current evidence boundary |
|---|---|---|
| UWBS-062..067 | **Accepted / Integrated** | post-v0.1.6 REC-03 reconciliation; accepted release boundaries |
| UWBS-068..078 | **Accepted / Integrated** | v0.1.6 CP-16X + REC-01 replay/reconciliation |
| UWBS-079 Stage A | **Accepted / Integrated** | v0.1.6 accepted boundary |
| UWBS-079 Stage B | **Pending / Experimental / Non-blocking** | longitudinal empirical-validation track; excluded from release blocker state |
| UWBS-080..086 | **Accepted / Integrated** | `v0.1.7` accepted / TAG READY |
| UWBS-087..093 | **Accepted / Integrated** | `v0.1.8` accepted / TAG READY |
| UWBS-094..100 | **Accepted / Integrated** | `v0.1.9` accepted / TAG READY |

## 3. Frozen collision namespace

The following provisional IDs are permanently frozen for new work:

```text
UWBS-101
UWBS-102
UWBS-103
UWBS-104
```

| Legacy reference | Historical meaning | Current canonical ID |
|---|---|---|
| UWBS-101 in PCE / Durable Goods / US-Japan rates / USDJPY / carry context | Macro Release Surprise / Yen Carry Flow Observability | **UWBS-105** |
| UWBS-101 in wallet / chain / contract / confirmed-transfer context | Crypto on-chain registry / transfer Fact | **UWBS-106** |
| UWBS-102 in abnormal-flow context | Crypto abnormal-flow metrics/state | **UWBS-107** |
| UWBS-103 in price/OI/funding/liquidation context | Crypto market-context join | **UWBS-108** |
| UWBS-104 in exploit/replay/NEAR Intents context | Crypto historical exploit / replay | **UWBS-109** |

If context is insufficient, mark the reference `AMBIGUOUS`; do not guess.

## 4. Current post-100 formal work

| UWBS | Formal WBS | Task | Current status | Release allocation |
|---|---|---|---|---|
| UWBS-105 | A0-018 | Macro Release Surprise / Yen Carry Flow Observability | **Incorporated / implementation pending** | **v0.1.12** |
| UWBS-106 | C0-001 | Cross-chain project/wallet/contract registry + confirmed-transfer Fact | **Accepted / Integrated** | **v0.1.11 REL-11A** |
| UWBS-107 | C0-002 | Abnormal on-chain flow Derived Metrics + candidate-state machine | **Accepted / Integrated** | **v0.1.11 REL-11B** |
| UWBS-108 | C0-003 | Join on-chain anomaly with price/OI/funding/liquidation context | **Accepted / Integrated** | **v0.1.11 REL-11C** |
| UWBS-109 | C0-004 | Historical exploit price-impact dataset + NEAR Intents replay | **Implementation pending / NEXT** | **v0.1.11 REL-11D** |

Canonical dependencies:

```text
Macro / v0.1.12:
A0-003 + A0-004 + A0-013..016
        -> A0-018 / UWBS-105
        -> existing A0-005 carry-unwind path

Crypto / v0.1.11:
C0-001 / UWBS-106  ACCEPTED
 -> C0-002 / UWBS-107  ACCEPTED
 -> C0-003 / UWBS-108  ACCEPTED
 -> C0-004 / UWBS-109  NEXT
UWBS-068..079 -> C0-003 / C0-004
```

## 5. Release CP

### v0.1.11

```text
REL-11A  C0-001 / UWBS-106  ACCEPTED / INTEGRATED
   -> REL-11B  C0-002 / UWBS-107  ACCEPTED / INTEGRATED
   -> REL-11C  C0-003 / UWBS-108  ACCEPTED / INTEGRATED
   -> REL-11D  C0-004 / UWBS-109  NEXT
   -> REL-11X  cumulative acceptance / TAG READY decision
```

### v0.1.12

```text
REL-12A  A0-018 macro release Fact / consensus / revision
   -> REL-12B  surprise + event-window transmission
   -> REL-12C  CARRY_BUILD / STABLE / COOLING integration
   -> existing A0-005 carry-unwind interpretation
   -> REL-12D  historical / revision / false-positive validation
   -> REL-12X  cumulative acceptance / TAG READY decision
```

## 6. Validation evidence retained

REL-11A:

```text
focused 9 passed
full analysis 1127 passed
compileall PASS
git diff --check PASS
```

REL-11B:

```text
focused C0-001+C0-002 19 passed
full analysis 1137 passed
compileall PASS
git diff --check PASS
```

REL-11C:

```text
focused C0-001+C0-002+C0-003 26 passed
full analysis 1144 passed
compileall PASS
git diff --check PASS
```

## 7. Current interpretation

```text
UWBS-062..100        ACCEPTED / INTEGRATED (except UWBS-079 Stage B non-blocking experiment)
UWBS-101..104        FROZEN CONFLICT / LEGACY-ONLY
UWBS-105             A0-018 — v0.1.12 PLANNED
UWBS-106             C0-001 — ACCEPTED / INTEGRATED
UWBS-107             C0-002 — ACCEPTED / INTEGRATED
UWBS-108             C0-003 — ACCEPTED / INTEGRATED
UWBS-109             C0-004 — NEXT
```

Next feature restart point is `v0.1.11 REL-11D / C0-004 / UWBS-109`. After v0.1.11 acceptance, the planned next release starts at `v0.1.12 REL-12A / A0-018 / UWBS-105`.
