# OrderScope — Current Critical Path Reconciliation

Status: **CURRENT DATE-INDEPENDENT OPERATING INDEX / v0.1.11 ACCEPTED**
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
- `REL_11X_V0_1_11_ACCEPTANCE_2026-10-03.md`

Historical dated CP documents and the integration pre-review remain evidence. They do not override the authorities above.

## 2. Accepted release state

```text
v0.1.0..v0.1.10  ACCEPTED / TAG READY
v0.1.11            ACCEPTED / TAG READY
```

Frozen validated target for `v0.1.11`:

```text
fce9a3a2e56783206d63dbcac0d8a65e50008c10
```

`TAG READY` is evidence only. This file does not authorize creation or push of Git tags.

## 3. Canonical namespace

```text
UWBS-101..104  FROZEN / CONFLICT / LEGACY-ONLY
UWBS-105       A0-018  Macro Release / Yen Carry Observability
UWBS-106       C0-001  Crypto registry + confirmed-transfer Fact
UWBS-107       C0-002  abnormal on-chain flow metrics/state
UWBS-108       C0-003  on-chain anomaly × market context
UWBS-109       C0-004  historical exploit / replay
```

## 4. v0.1.11 completion

```text
REL-11A  C0-001 / UWBS-106  ACCEPTED / INTEGRATED
REL-11B  C0-002 / UWBS-107  ACCEPTED / INTEGRATED
REL-11C  C0-003 / UWBS-108  ACCEPTED / INTEGRATED
REL-11D  C0-004 / UWBS-109  ACCEPTED / INTEGRATED
REL-11X  cumulative acceptance  ACCEPTED / TAG READY
```

Accepted cumulative validation:

```text
crypto_onchain                33 passed
crypto_context/derivatives/
archive/time/canary          111 passed
full analysis               1151 passed
compileall                   PASS
git diff --check             PASS
```

## 5. Current release CP — v0.1.12

```text
REL-12A
A0-018 stage 1
Macro release Fact / consensus / prior / revision contract
(PCE / Durable Goods initial families)
        |
        v
REL-12B
Deterministic surprise + bounded event-window transmission
(30m / 2h / 1d; US2Y / JP2Y / spread / USDJPY)
        |
        v
REL-12C
CARRY_BUILD / CARRY_STABLE / CARRY_COOLING
        |
        v
existing A0-005
CARRY_UNWIND_CANDIDATE / DELEVERAGING_REGIME
        |
        v
REL-12D
Historical / revision / stale-market / contradiction / false-positive validation
        |
        v
REL-12X
Cumulative v0.1.12 acceptance / TAG READY decision
```

A0-018 extends accepted A0-003/A0-004/A0-013..016 and feeds the existing A0-005 carry-unwind path. It must not claim observed capital flow without a direct eligible flow source.

## 6. Selected restart point

```text
NEXT RELEASE: v0.1.12
  -> REL-12A / A0-018 / UWBS-105
```

## 7. Restart rule

After interruption:

1. read this file;
2. read `CURRENT_CRITICAL_PATH_RECONCILIATION_2026-10-03.md`;
3. read `CURRENT_UWBS_PROGRESS_TRACKER.md`;
4. use `WBS_PROVISIONAL_ID_REGISTRY.md` for identifier authority;
5. use the final tag ledger for v0.1.0..v0.1.10;
6. use `REL_11X_V0_1_11_ACCEPTANCE_2026-10-03.md` for the v0.1.11 frozen target;
7. never restart accepted C0-001..004 work;
8. resume from `v0.1.12 REL-12A / A0-018 / UWBS-105`.

No provider activation, Worker/Cron mutation, D1 mutation, paid procurement, live PB execution, automated trading, tag creation, history rewrite, or force push is authorized by this index.
