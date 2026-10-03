# OrderScope — Current Critical Path Reconciliation — 2026-10-03

Status: **CURRENT OPERATING INDEX CANDIDATE**
Scope: Release management + market-independent feature governance

## 1. Authority rule

This document supersedes the 2026-10-02 critical-path candidate for current planning purposes.
Historical acceptance and release evidence remain immutable.

Companion current authorities:

- `CURRENT_UWBS_PROGRESS_TRACKER.md`
- `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
- `WBS_PROVISIONAL_ID_REGISTRY.md`
- `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
- `docs/release/V0_1_0_TO_V0_1_10_FINAL_TAG_LEDGER_2026-10-03.md`
- `docs/release/V0_1_11_UWBS_NAMESPACE_CORRECTION_2026-10-03.md`

No CP statement authorizes provider activation, Worker/Cron mutation, D1 mutation, paid procurement, PB execution, automated trading, or security-incident assertion unless separately approved.

## 2. Reconciled accepted feature state

```text
UWBS-062..067  AI Theme / Listing Compliance             ACCEPTED / INTEGRATED
UWBS-068..078  Crypto Market Structure                   ACCEPTED / INTEGRATED
UWBS-079 A     Weekend re-risk Stage A                    ACCEPTED / INTEGRATED
UWBS-079 B     Longitudinal experiment                    PENDING / NON-BLOCKING
UWBS-080..086  Oil / Commodity / Cross-Asset             ACCEPTED / INTEGRATED
UWBS-087..093  Physical-SaaS                             ACCEPTED / INTEGRATED
UWBS-094..100  VIX / Cross-Asset Volatility              ACCEPTED / INTEGRATED
```

Older restart points at UWBS-080, UWBS-088, PB-09 or UWBS-101 are stale and must not cause accepted work to be repeated.

## 3. Release authority through v0.1.10

The final release ledger fixes the following exact targets:

```text
v0.1.0  99b08a0b5fa1bec5921dc42e630c579a4e83c401  ACCEPTED / TAG READY
v0.1.1  bada5bff803321427eb3c8eb1f3d159460ba5dd1  ACCEPTED / TAG READY
v0.1.2  f69c52bf574212d1506df81abc7b15694abb7922  ACCEPTED / TAG READY
v0.1.3  b4df4e911597d9f17bfa0a50b2057c24159dee9f  ACCEPTED / TAG READY
v0.1.4  a798622f839b836f8b60f52dd700b8fd87147991  ACCEPTED / TAG READY
v0.1.5  415de1f1dd42f70bd66992961cb43be7edba6ade  ACCEPTED / TAG READY
v0.1.6  bfaf89c68daa656b7d75317f086458257cc94da9  ACCEPTED / TAG READY
v0.1.7  423929ae1ff3fd7431260ffdab09810dc7105aa0  ACCEPTED / TAG READY
v0.1.8  d34d471b20d4f5be865b0414a42240ec7f3061d9  ACCEPTED / TAG READY
v0.1.9  fcfba651dbead9d035019e330f61986f5a1a60f7  ACCEPTED / TAG READY
v0.1.10 c1e27d8367c490543e1d207f62d77f3bb5e8bc4e  ACCEPTED / TAG READY
```

`TAG READY` is release-state evidence only. No annotated tag creation or push is authorized by this document.

## 4. UWBS-101..104 namespace freeze

The identifiers below are frozen permanently for new planning and implementation:

```text
UWBS-101
UWBS-102
UWBS-103
UWBS-104
```

They are historical collision aliases only.

Contextual mapping:

```text
Macro legacy UWBS-101
  -> UWBS-105

Crypto legacy UWBS-101
  -> UWBS-106
Crypto legacy UWBS-102
  -> UWBS-107
Crypto legacy UWBS-103
  -> UWBS-108
Crypto legacy UWBS-104
  -> UWBS-109
```

If the surrounding text does not identify the intended lane, classify the reference as `AMBIGUOUS` rather than assigning a number.

## 5. Current market-independent CP

### 5.1 Release-management branch

All reconstructed versions through `v0.1.10` are accepted and tag-ready.
The remaining release-management action is documentation/authority synchronization and, only if separately authorized later, tag creation.

```text
v0.1.0..v0.1.10 exact-boundary reconciliation  [ACCEPTED]
        |
        v
CURRENT management-file synchronization         [IN PROGRESS]
        |
        +--> no tag creation without explicit authorization
```

### 5.2 Macro / Carry planning branch

Canonical new task:

```text
UWBS-011 + UWBS-012
        |
        v
UWBS-105  Macro Release Surprise / Yen Carry Flow Observability [PLANNED]
        |
        v
existing UWBS-013 carry-unwind / deleveraging interpretation
```

UWBS-105 includes official PCE / Durable Goods release Facts, consensus/revision provenance, deterministic surprise metrics, bounded event-window rate/FX transmission, and BUILD/STABLE/COOLING carry-state interpretation.

This work is WBS-unreflected and is not automatically part of `v0.1.11`.

### 5.3 Crypto On-chain Event Intelligence / v0.1.11

Canonical planned sequence:

```text
REL-11A / UWBS-106
  Cross-chain wallet/component registry
  + confirmed-transfer Fact contract
        |
        v
REL-11B / UWBS-107
  Abnormal on-chain flow Derived Metrics
  + candidate-state machine
        |
        v
REL-11C / UWBS-108
  Join anomaly with price / OI / funding / liquidation context
        |
        v
REL-11D / UWBS-109
  Historical exploit price-impact dataset
  + NEAR Intents replay
        |
        v
REL-11X
  cumulative v0.1.11 acceptance / tag-ready decision
```

Additional accepted dependencies:

```text
UWBS-068..079 -> UWBS-108
UWBS-068..079 -> UWBS-109
```

No task may infer a confirmed security incident solely from abnormal transfers or market movement.

## 6. Market-dependent PB lane

The final release ledger records the PB closeout as part of accepted `v0.1.10`.
Therefore older tracker statements such as:

```text
PB-09 execution pending
PB-10 not authorized / not executed
```

are historical intermediate states, not the current release blocker state.

Current interpretation:

```text
PB-00..PB-10 closeout boundary  ACCEPTED / TAG READY as v0.1.10
```

Any new live market execution is a new operational action and still requires fresh authorization; accepted historical PB closeout does not grant standing permission for future live execution.

## 7. Selected restart point

For management work:

```text
CURRENT: synchronize remaining CURRENT / WBS / release authorities
NEXT:    formal WBS/backlog incorporation of canonical post-100 IDs
```

For new feature implementation after management reconciliation:

```text
Macro lane:  UWBS-105
Crypto lane: UWBS-106 -> UWBS-107 -> UWBS-108 -> UWBS-109
```

The implementation order between UWBS-105 and the v0.1.11 crypto lane is a planning decision; this document does not silently prioritize one over the other.

## 8. Restart rule

After interruption:

1. read this file;
2. read `CURRENT_UWBS_PROGRESS_TRACKER.md`;
3. use `WBS_PROVISIONAL_ID_REGISTRY.md` for provisional IDs;
4. use the final tag ledger for release boundaries;
5. never restart work from legacy UWBS-101..104;
6. never repeat accepted UWBS-080..100 or PB-00..PB-10 closeout;
7. resume management synchronization first while it remains incomplete;
8. when implementation resumes, use canonical UWBS-105 or UWBS-106..109 only.
