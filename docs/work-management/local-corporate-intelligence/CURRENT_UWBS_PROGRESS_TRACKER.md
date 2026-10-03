# OrderScope — Current UWBS Progress Tracker

Status: **CURRENT UWBS OVERLAY**
Updated: 2026-10-03

This tracker is the current UWBS-specific overlay for canonical task progress. Historical evidence remains immutable; current planning references use canonical IDs.

## 1. Accepted / integrated ranges

| UWBS range | Current status |
|---|---|
| UWBS-062..067 | **Accepted / Integrated** |
| UWBS-068..078 | **Accepted / Integrated** |
| UWBS-079 Stage A | **Accepted / Integrated** |
| UWBS-079 Stage B | **Pending / Experimental / Non-blocking** |
| UWBS-080..100 | **Accepted / Integrated** |

## 2. Frozen collision namespace

```text
UWBS-101..104  FROZEN / CONFLICT / LEGACY-ONLY
```

Contextual remapping remains:

```text
Macro legacy UWBS-101 -> UWBS-105 -> A0-018
Crypto legacy UWBS-101 -> UWBS-106 -> C0-001
Crypto legacy UWBS-102 -> UWBS-107 -> C0-002
Crypto legacy UWBS-103 -> UWBS-108 -> C0-003
Crypto legacy UWBS-104 -> UWBS-109 -> C0-004
```

## 3. Current post-100 formal work

| UWBS | Formal WBS | Task | Current status | Release allocation |
|---|---|---|---|---|
| UWBS-105 | A0-018 | Macro Release Surprise / Yen Carry Flow Observability | **Implementation pending / NEXT** | **v0.1.12 REL-12A..D** |
| UWBS-106 | C0-001 | Cross-chain project/wallet/contract registry + confirmed-transfer Fact | **Accepted / Integrated** | **v0.1.11 REL-11A** |
| UWBS-107 | C0-002 | Abnormal on-chain flow Derived Metrics + candidate-state machine | **Accepted / Integrated** | **v0.1.11 REL-11B** |
| UWBS-108 | C0-003 | Join on-chain anomaly with price/OI/funding/liquidation context | **Accepted / Integrated** | **v0.1.11 REL-11C** |
| UWBS-109 | C0-004 | Historical exploit price-impact dataset + replay | **Accepted / Integrated** | **v0.1.11 REL-11D** |

## 4. Release state

```text
v0.1.10  ACCEPTED / TAG READY
v0.1.11  ACCEPTED / TAG READY
v0.1.12  NEXT / IMPLEMENTATION PENDING
```

Validated v0.1.11 target:

```text
fce9a3a2e56783206d63dbcac0d8a65e50008c10
```

## 5. v0.1.11 cumulative evidence

```text
crypto_onchain                33 passed
crypto_context/derivatives/
archive/time/canary          111 passed
full analysis               1151 passed
compileall                   PASS
git diff --check             PASS
```

## 6. Current CP

```text
v0.1.11
REL-11A..D / C0-001..004 / UWBS-106..109  ACCEPTED / INTEGRATED
REL-11X                                      ACCEPTED / TAG READY

v0.1.12
REL-12A / A0-018 / UWBS-105                 NEXT
 -> REL-12B
 -> REL-12C
 -> existing A0-005 unwind/deleveraging path
 -> REL-12D
 -> REL-12X
```

`TAG READY` does not authorize creation or push of a Git tag.

## 7. Current interpretation

```text
UWBS-062..100        ACCEPTED / INTEGRATED (except UWBS-079 Stage B non-blocking experiment)
UWBS-101..104        FROZEN CONFLICT / LEGACY-ONLY
UWBS-105             A0-018 — v0.1.12 NEXT
UWBS-106..109        C0-001..004 — ACCEPTED / INTEGRATED / v0.1.11 TAG READY
```

Next feature restart point is `v0.1.12 REL-12A / A0-018 / UWBS-105`.
