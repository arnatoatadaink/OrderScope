# OrderScope — Current UWBS Progress Tracker

Status: **CURRENT UWBS OVERLAY**
Updated: 2026-10-03

This tracker is the current UWBS-specific overlay for canonical task progress. It supplements historical acceptance records and older integrated trackers.

Canonical ID meanings are governed by `WBS_PROVISIONAL_ID_REGISTRY.md`.
Namespace collision handling is governed by `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`.
Release boundaries through `v0.1.10` are governed by `docs/release/V0_1_0_TO_V0_1_10_FINAL_TAG_LEDGER_2026-10-03.md`.

## 1. Status rule

A UWBS item is not downgraded merely because its original branch is old or diverged. Use the newest accepted evidence in this order:

1. accepted task/local-validation evidence;
2. reconciliation / selective-replay evidence;
3. cumulative release acceptance / tag-ready evidence;
4. current namespace and WBS authority.

Historical evidence remains immutable. Current planning references must use canonical IDs.

## 2. Accepted / integrated ranges

| UWBS range | Current status | Current evidence boundary |
|---|---|---|
| UWBS-062..067 | **Accepted / Integrated** | post-v0.1.6 REC-03 reconciliation; `v0.1.4` / `v0.1.5` accepted release boundaries |
| UWBS-068..078 | **Accepted / Integrated** | v0.1.6 CP-16X + REC-01 replay/reconciliation |
| UWBS-079 Stage A | **Accepted / Integrated** | v0.1.6 accepted boundary |
| UWBS-079 Stage B | **Pending / Experimental / Non-blocking** | longitudinal empirical-validation track; excluded from release blocker state |
| UWBS-080..086 | **Accepted / Integrated** | `v0.1.7` accepted / TAG READY |
| UWBS-087..093 | **Accepted / Integrated** | `v0.1.8` accepted / TAG READY |
| UWBS-094..100 | **Accepted / Integrated** | `v0.1.9` accepted / TAG READY |

## 3. v0.1.6 provenance detail

| UWBS | Status | Implementation provenance | Acceptance / integration provenance |
|---|---|---|---|
| UWBS-062 | **Accepted / Integrated** | `theme/ontology.py` | REC-03 replay `9a40e29112e0cfae50828be7270cf1995ec53b97`; acceptance `b3f18252f9ad3efdf17ea8c1c2ddea8dcf838861` |
| UWBS-063 | **Accepted / Integrated** | `theme/reaction.py` | REC-03 replay / acceptance |
| UWBS-064 | **Accepted / Integrated** | `theme/observation.py` | REC-03 replay / acceptance |
| UWBS-065 | **Accepted / Integrated** | `theme/state.py` | REC-03 replay / acceptance |
| UWBS-066 | **Accepted / Integrated** | `theme/calibration.py` | REC-03 replay / acceptance |
| UWBS-067 | **Accepted / Integrated** | `codex/uwbs-067-listing-compliance` @ `44e7a2d31c6ef5ebebafb77fbe44ac307625b014` | REC-03 selective replay / acceptance |
| UWBS-068 | **Accepted / Integrated** | `codex/uwbs-068-crypto-derivatives-contract` @ `716644a679f8f353d409e48ec06351dc38c2060e` | v0.1.6 CP-16X; REC-01 replay |
| UWBS-069 | **Accepted / Integrated** | `codex/uwbs-069-btc-relative-context` @ `56cd68aabd06326041acc8a37dc458f6cc3beb2f` | v0.1.6 CP-16X; current `crypto_context` package |
| UWBS-070 | **Accepted / Integrated planning evidence** | no dedicated task branch identified | CP-070A accepted in v0.1.6 progress reflection |
| UWBS-071 | **Accepted / Integrated** | `codex/uwbs-071-crypto-time-windows` @ `1cbcb9b65bbbea3b1ac251d614201d8d2ca86d5f` | v0.1.6 CP-16X; REC-01/current `crypto_time` |
| UWBS-072 | **Accepted / Integrated** | `codex/uwbs-072-near-btc-canary` @ `4ea346dfab96b1a2ba1e685bf6daba27341445a0` | v0.1.6 CP-16X; REC-01/current `crypto_canary` |
| UWBS-073 | **Accepted / Integrated** | `codex/uwbs-073-multivenue-adapters` @ `d602de71a93b8ac8c8877c0d0114d66553046555` | v0.1.6 CP-16X; REC-01 |
| UWBS-074 | **Accepted / Integrated** | `codex/uwbs-074-derivatives-archive` @ `4c34a8f36f1083f84d46a788f62b9e7b05ad4adc` | v0.1.6 CP-16X; REC-01/current `crypto_archive` |
| UWBS-075 | **Accepted / Integrated** | `codex/uwbs-075-liquidation-cascade` @ `aece57aa74fd89e9ca975668c6f00817aa442d25` | v0.1.6 CP-16X; REC-01 |
| UWBS-076 | **Accepted / Integrated** | `codex/uwbs-076-position-map-oi-retention` @ `a0cfe87e2f22fd470b97ca218959ef45eb668128` | v0.1.6 CP-16X; REC-01 |
| UWBS-077 | **Accepted / Integrated** | `codex/uwbs-077-cross-venue-qa` @ `1348ff64520fee5f0215591a985b36b6fb66e8e8` | v0.1.6 CP-16X; REC-01 |
| UWBS-078 | **Accepted / Integrated** | `codex/uwbs-078-near-futures-position-canary` @ `50d3b0697b8c6e07e4bab22c7faec11472154249` | v0.1.6 CP-16X; REC-01 |
| UWBS-079 Stage A | **Accepted / Integrated** | `codex/uwbs-079-weekend-rerisk-validation` @ `bf1a6294bf18ee2fad81a140e8a52b46b5f96c20` | v0.1.6 CP-16X; REC-01 |
| UWBS-079 Stage B | **Pending / Experimental** | longitudinal empirical-validation track | non-blocking |

## 4. Accepted post-v0.1.6 lanes

### UWBS-080..086 — Oil / Commodity / Cross-Asset

Status: **Accepted / Integrated / v0.1.7 TAG READY**

Final cumulative release target:

```text
423929ae1ff3fd7431260ffdab09810dc7105aa0
```

### UWBS-087..093 — Physical-SaaS

Status: **Accepted / Integrated / v0.1.8 TAG READY**

Final cumulative release target:

```text
d34d471b20d4f5be865b0414a42240ec7f3061d9
```

### UWBS-094..100 — VIX / Cross-Asset Volatility

Status: **Accepted / Integrated / v0.1.9 TAG READY**

Final cumulative release target:

```text
fcfba651dbead9d035019e330f61986f5a1a60f7
```

These accepted lanes must not be reopened merely because older CURRENT trackers still show intermediate states.

## 5. Frozen collision namespace

The following provisional IDs are **permanently frozen for new work**:

```text
UWBS-101
UWBS-102
UWBS-103
UWBS-104
```

Reason: two post-100 planning streams reused the same namespace before a canonical registry update.

Historical references are retained as provenance. They do not define active current task identity.

Contextual historical mapping:

| Legacy reference | Historical meaning | Current canonical ID |
|---|---|---|
| UWBS-101 in PCE / Durable Goods / US-Japan rates / USDJPY / carry context | Macro Release Surprise / Yen Carry Flow Observability | **UWBS-105** |
| UWBS-101 in wallet / chain / contract / confirmed-transfer context | Crypto on-chain registry / transfer Fact | **UWBS-106** |
| UWBS-102 in abnormal-flow context | Crypto abnormal-flow metrics/state | **UWBS-107** |
| UWBS-103 in price/OI/funding/liquidation context | Crypto market-context join | **UWBS-108** |
| UWBS-104 in exploit/replay/NEAR Intents context | Crypto historical exploit / replay | **UWBS-109** |

If context is insufficient, mark the reference `AMBIGUOUS`; do not guess.

## 6. Current post-100 planned work

| UWBS | Task | Current status | Release allocation |
|---|---|---|---|
| UWBS-105 | Macro Release Surprise / Yen Carry Flow Observability | **Planned / WBS-unreflected** | Separate Macro/Carry planning item; not included in v0.1.11 by default |
| UWBS-106 | Cross-chain protocol wallet/component registry + confirmed-transfer Fact | **Planned / Not implemented** | v0.1.11 Crypto On-chain Event Intelligence |
| UWBS-107 | Abnormal on-chain flow Derived Metrics + candidate-state machine | **Planned / Not implemented** | v0.1.11 |
| UWBS-108 | Join on-chain anomaly with price/OI/funding/liquidation context | **Planned / Not implemented** | v0.1.11 |
| UWBS-109 | Historical exploit price-impact dataset + NEAR Intents replay | **Planned / Not implemented** | v0.1.11 |

Canonical dependencies:

```text
Macro:
UWBS-011 + UWBS-012
        -> UWBS-105
        -> existing UWBS-013 carry-unwind path

Crypto:
UWBS-106 -> UWBS-107 -> UWBS-108 -> UWBS-109
UWBS-068..079 -> UWBS-108
UWBS-068..079 -> UWBS-109
```

## 7. Release-state note

The reconstructed accepted release ledger currently fixes:

```text
v0.1.6  UWBS-068..079 Stage-A boundary      ACCEPTED / TAG READY
v0.1.7  UWBS-080..086                       ACCEPTED / TAG READY
v0.1.8  UWBS-087..093                       ACCEPTED / TAG READY
v0.1.9  UWBS-094..100                       ACCEPTED / TAG READY
v0.1.10 PB-00..PB-10 closeout               ACCEPTED / TAG READY
v0.1.11 UWBS-106..109                       PLANNED
```

`TAG READY` does not mean that the annotated Git tag has been created or pushed.

## 8. Validation evidence retained

v0.1.6 CP-16X:

```text
crypto_derivatives  62 passed
crypto_canary       20 passed
crypto_context       9 passed
crypto_time         10 passed
crypto_archive      10 passed
full analysis      746 passed, 1 warning
compileall          PASS
git diff --check    PASS
```

Post-v0.1.6 cumulative reconciliation:

```text
crypto_derivatives   62 passed
crypto_canary        20 passed
crypto_context        9 passed
crypto_time          10 passed
crypto_archive       10 passed
listing_compliance    9 passed
theme                 12 passed
full analysis       1118 passed
Worker               227 passed / 0 failed
compileall            PASS
git diff --check      PASS
npm typecheck         PASS
```

v0.1.10 final PB reconstruction:

```text
Python full         1097 passed
compileall          PASS
Worker              228 passed / 0 failed
Worker typecheck    PASS
git diff --check    PASS
```

## 9. Current interpretation

```text
UWBS-062..067        ACCEPTED / INTEGRATED
UWBS-068..078        ACCEPTED / INTEGRATED
UWBS-079 Stage A     ACCEPTED / INTEGRATED
UWBS-079 Stage B     PENDING / EXPERIMENTAL / NON-BLOCKING
UWBS-080..100        ACCEPTED / INTEGRATED
UWBS-101..104        FROZEN CONFLICT / LEGACY-ONLY
UWBS-105             PLANNED — MACRO/CARRY
UWBS-106..109        PLANNED — v0.1.11 CRYPTO ON-CHAIN EVENT INTELLIGENCE
```

Future UWBS progress updates should record canonical ID, branch/commit provenance, acceptance evidence, release allocation, and current integration state.
