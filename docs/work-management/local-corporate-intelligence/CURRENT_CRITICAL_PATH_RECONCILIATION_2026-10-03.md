# OrderScope — Current Critical Path Reconciliation — 2026-10-03

Status: **CURRENT OPERATING CP AUTHORITY / FEATURE IMPLEMENTATION IN PROGRESS**
Scope: Release management + market-independent feature governance

## 1. Authority rule

This document is the detailed current CP authority after the 2026-10-03 management refresh was integrated into `main`. Historical acceptance and release evidence remain immutable.

No CP statement authorizes provider activation, Worker/Cron mutation, D1 mutation, paid procurement, PB execution, automated trading, tag creation, or security-incident assertion unless separately approved.

## 2. Current accepted feature state

```text
UWBS-062..067  ACCEPTED / INTEGRATED
UWBS-068..078  ACCEPTED / INTEGRATED
UWBS-079 A     ACCEPTED / INTEGRATED
UWBS-079 B     PENDING / NON-BLOCKING
UWBS-080..100  ACCEPTED / INTEGRATED
UWBS-106       C0-001 / REL-11A  ACCEPTED / INTEGRATED
UWBS-107       C0-002 / REL-11B  ACCEPTED / INTEGRATED
UWBS-108       C0-003 / REL-11C  ACCEPTED / INTEGRATED
```

## 3. Release authority through v0.1.10

The final release ledger remains authoritative for exact v0.1.0..v0.1.10 targets. `TAG READY` does not authorize tag creation or push.

## 4. Namespace freeze

`UWBS-101..104` remain permanently frozen as historical collision aliases only.

```text
Macro legacy UWBS-101 -> UWBS-105 -> A0-018
Crypto legacy UWBS-101 -> UWBS-106 -> C0-001
Crypto legacy UWBS-102 -> UWBS-107 -> C0-002
Crypto legacy UWBS-103 -> UWBS-108 -> C0-003
Crypto legacy UWBS-104 -> UWBS-109 -> C0-004
```

## 5. Release sequence

```text
v0.1.10  ACCEPTED / TAG READY
   -> v0.1.11  Crypto On-chain Event Intelligence  IN PROGRESS
   -> v0.1.12  Macro Release / Yen Carry Observability  PLANNED
```

## 6. v0.1.11 CP

```text
REL-11A  C0-001 / UWBS-106  ACCEPTED / INTEGRATED
   -> REL-11B  C0-002 / UWBS-107  ACCEPTED / INTEGRATED
   -> REL-11C  C0-003 / UWBS-108  ACCEPTED / INTEGRATED
   -> REL-11D  C0-004 / UWBS-109  NEXT
   -> REL-11X  cumulative v0.1.11 acceptance / TAG READY decision
```

Accepted `UWBS-068..079` market-structure evidence feeds REL-11C and REL-11D. No abnormal transfer or market movement alone may be promoted to a confirmed security incident.

REL-11X still requires cumulative C0 tests, affected accepted crypto-market-structure tests, full Python regression, compileall, diff checks, and affected Worker checks when shared runtime contracts change.

## 7. v0.1.12 CP

`A0-018 / UWBS-105` remains planned for v0.1.12 after v0.1.11 cumulative acceptance under the current release sequence. It has no technical dependency on C0-001..004.

## 8. Selected restart point

```text
NEXT: REL-11D / C0-004 / UWBS-109
```

After v0.1.11 acceptance:

```text
v0.1.12 REL-12A / A0-018 / UWBS-105
```

## 9. Restart rule

After interruption, read the date-independent CURRENT CP, this detailed CP, CURRENT UWBS tracker, release plan, and provisional-ID registry. Never repeat accepted REL-11A..REL-11C; resume at REL-11D.
