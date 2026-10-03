# OrderScope — Current Critical Path Reconciliation — 2026-10-03

Status: **CURRENT OPERATING CP AUTHORITY / MANAGEMENT INTEGRATED**
Scope: Release management + market-independent feature governance

## 1. Authority rule

This document is the detailed current CP authority after the 2026-10-03 management refresh was squash-merged into `main`.
Historical acceptance and release evidence remain immutable.

Management integration commit:

```text
f9dc1270db8d3b167a163edd8a0475747e2a404b
```

Companion current authorities:

- `CURRENT_CRITICAL_PATH_RECONCILIATION.md`
- `CURRENT_UWBS_PROGRESS_TRACKER.md`
- `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
- `WBS_PROVISIONAL_ID_REGISTRY.md`
- `UWBS_101_104_NAMESPACE_RECONCILIATION_2026-10-03.md`
- `docs/release/V0_1_0_TO_V0_1_10_FINAL_TAG_LEDGER_2026-10-03.md`
- `docs/release/V0_1_11_UWBS_NAMESPACE_CORRECTION_2026-10-03.md`
- `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`
- `docs/WORK_BREAKDOWN_CRYPTO_ONCHAIN_EVENT_INTELLIGENCE_2026-10-03.md`
- `docs/WORK_BREAKDOWN_ANALYST_CROSS_MARKET_POST100_2026-10-03.md`

No CP statement authorizes provider activation, Worker/Cron mutation, D1 mutation, paid procurement, PB execution, automated trading, or security-incident assertion unless separately approved.

## 2. Reconciled accepted feature state

```text
UWBS-062..067  AI Theme / Listing Compliance             ACCEPTED / INTEGRATED
UWBS-068..078  Crypto Market Structure                   ACCEPTED / INTEGRATED
UWBS-079 A     Weekend re-risk Stage A                   ACCEPTED / INTEGRATED
UWBS-079 B     Longitudinal experiment                   PENDING / NON-BLOCKING
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
Macro legacy UWBS-101 -> UWBS-105 -> A0-018
Crypto legacy UWBS-101 -> UWBS-106 -> C0-001
Crypto legacy UWBS-102 -> UWBS-107 -> C0-002
Crypto legacy UWBS-103 -> UWBS-108 -> C0-003
Crypto legacy UWBS-104 -> UWBS-109 -> C0-004
```

If surrounding text does not identify the intended lane, classify the reference as `AMBIGUOUS` rather than assigning a number.

## 5. Planned release sequence after v0.1.10

```text
v0.1.10  PB / active-market validation closeout    ACCEPTED / TAG READY
   |
   v
v0.1.11  Crypto On-chain Event Intelligence        PLANNED / IMPLEMENTATION PENDING
   |
   v
v0.1.12  Macro Release / Yen Carry Observability   PLANNED / IMPLEMENTATION PENDING
```

The ordering of v0.1.11 before v0.1.12 is a release-management decision. A0-018 does not technically depend on C0-001..004.

## 6. v0.1.11 — Crypto On-chain Event Intelligence CP

Formal WBS: `C0-001..004`
Canonical provisional IDs: `UWBS-106..109`

```text
REL-11A
C0-001 / UWBS-106
Cross-chain project / wallet / contract registry
+ confirmed-transfer Fact contract
        |
        v
REL-11B
C0-002 / UWBS-107
Abnormal on-chain flow Derived Metrics
+ candidate-state machine
        |
        v
REL-11C
C0-003 / UWBS-108
On-chain anomaly × market-context join
(price / BTC-relative / OI / funding / liquidation)
        |
        v
REL-11D
C0-004 / UWBS-109
Historical exploit price-impact dataset
+ NEAR Intents replay / false-positive validation
        |
        v
REL-11X
Cumulative v0.1.11 regression / acceptance / TAG READY decision
```

Accepted dependency edges:

```text
UWBS-068..079 -> REL-11C / C0-003
UWBS-068..079 -> REL-11D / C0-004
```

No task may infer a confirmed security incident solely from abnormal transfers or market movement.

### v0.1.11 acceptance gate

REL-11X requires:

- C0 focused tests pass;
- affected accepted crypto-market-structure tests pass;
- full Python regression passes;
- compileall and `git diff --check` pass;
- affected Worker tests/typecheck pass when shared runtime contracts change;
- replay preserves first-on-chain/public/official timestamp distinctions;
- candidate abnormal flow remains distinct from confirmed incident attribution.

## 7. v0.1.12 — Macro Release / Yen Carry Observability CP

Formal WBS: `A0-018`
Canonical provisional ID: `UWBS-105`

Existing accepted foundations reused:

```text
A0-003  Macro-Market non-price Fact
A0-004  Rate-curve / cross-country Derived Metrics
A0-005  Carry-unwind / deleveraging Interpretation
A0-007  Macro-rate / FX provider/source selection
A0-013..016 official / fallback macro source adapters
```

Implementation CP:

```text
REL-12A
A0-018 stage 1
Macro release Fact / consensus / prior / revision contract
(PCE / Durable Goods initial families)
        |
        v
REL-12B
A0-018 stage 2
Deterministic release surprise
+ no-lookahead event-window transmission
(30m / 2h / 1d; US2Y / JP2Y / spread / USDJPY)
        |
        v
REL-12C
A0-018 stage 3
CARRY_BUILD / CARRY_STABLE / CARRY_COOLING
        |
        v
existing A0-005
CARRY_UNWIND_CANDIDATE / DELEVERAGING_REGIME
        |
        v
REL-12D
A0-018 stage 4
Historical fixtures / revisions / stale-market /
contradiction / false-positive validation
        |
        v
REL-12X
Cumulative v0.1.12 regression / acceptance / TAG READY decision
```

Formal dependency relation:

```text
A0-003 + A0-004 + A0-013..016
        |
        v
A0-018 / UWBS-105
        |
        v
A0-005 existing carry-unwind interpretation path
```

### v0.1.12 acceptance gate

REL-12X requires:

- official-release timestamps/provenance preserved;
- actual/consensus/prior/revision values explicit;
- deterministic unit-safe surprise computation;
- no-lookahead reproducible event windows;
- stale or closed-market observations remain UNKNOWN;
- contradictory evidence remains inspectable;
- `CARRY_BUILD/STABLE/COOLING` remain Interpretation rather than observed flow Fact;
- `CARRY_UNWIND_CANDIDATE` still requires independent A0-005 evidence;
- focused A0-018 and affected Macro/Cross-Market tests pass;
- full Python regression, compileall and diff checks pass.

## 8. Market-dependent PB lane

The final release ledger records the PB closeout as part of accepted `v0.1.10`.
Older tracker statements such as `PB-09 execution pending` or `PB-10 not authorized / not executed` are historical intermediate states, not current release blockers.

Current interpretation:

```text
PB-00..PB-10 closeout boundary  ACCEPTED / TAG READY as v0.1.10
```

Any new live market execution is a new operational action and still requires fresh authorization.

## 9. Selected restart point

Management-file reconciliation through MFR-06, authority-drift review, and squash integration are complete.

Current feature restart:

```text
NEXT RELEASE: v0.1.11
  -> REL-11A / C0-001 / UWBS-106

AFTER v0.1.11 acceptance:
  -> v0.1.12 REL-12A / A0-018 / UWBS-105
```

A0-018 may technically be developed independently, but current release sequencing keeps its cumulative acceptance target at v0.1.12.

## 10. Restart rule

After interruption:

1. read `CURRENT_CRITICAL_PATH_RECONCILIATION.md` as the date-independent entry point;
2. read this file for detailed CP;
3. read `CURRENT_UWBS_PROGRESS_TRACKER.md`;
4. read `docs/release/V0_1_11_V0_1_12_RELEASE_PLAN_2026-10-03.md`;
5. use `WBS_PROVISIONAL_ID_REGISTRY.md` for provisional IDs;
6. use the final tag ledger for accepted release boundaries through v0.1.10;
7. never restart work from legacy UWBS-101..104;
8. never repeat accepted UWBS-080..100 or PB-00..PB-10 closeout;
9. resume v0.1.11 from the first incomplete REL-11 unit;
10. after v0.1.11 acceptance, resume v0.1.12 from the first incomplete REL-12 unit.
