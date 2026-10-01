# OrderScope — Current Critical Path Reconciliation — 2026-10-02

Status: **CURRENT OPERATING INDEX CANDIDATE**
Scope: Release management + market-independent feature governance
Branch: `docs/v0-1-10-release-cp`

## 1. Authority rule

This document is the 2026-10-02 successor to the older date-independent reconciliation where the selected restart point was still `UWBS-080`.

Accepted historical evidence remains immutable. This reconciliation advances the restart point using later accepted implementation and release-reconciliation evidence.

Companion authorities:

- `CURRENT_LOCAL_CORPORATE_INTELLIGENCE_PROGRESS_TRACKER.md`
- `WBS_PROVISIONAL_ID_REGISTRY.md`
- `docs/release/V0_1_VERSION_BOUNDARY_PLAN_2026-09-28.md`
- `docs/release/POST_V0_1_6_MAIN_INTEGRATION_REVIEW_2026-10-01.md`
- `docs/release/V0_1_7_TO_V0_1_10_RELEASE_CP_2026-10-02.md`
- `WBS_UNREFLECTED_CRYPTO_ONCHAIN_SECURITY_EXTENSION_2026-10-02.md`

## 2. Reconciled accepted feature state

The previous market-independent restart chain has advanced beyond the 9/27 planning snapshot.

```text
UWBS-080..086  Oil / commodity / cross-asset             ACCEPTED
UWBS-087..093  Physical-SaaS                             ACCEPTED
UWBS-094..100  VIX / cross-asset volatility              ACCEPTED
```

Post-v0.1.6 cumulative reconciliation has also been accepted and integrated to main through the approved fast-forward path.

The old restart instructions that point to UWBS-080 or UWBS-088 are historical and must not cause accepted work to be repeated.

## 3. Release lane becomes the current selected CP

The user-selected work order is release management first.

```text
REL-07  confirm v0.1.7 boundary
  -> REL-08  confirm v0.1.8 boundary
  -> REL-09  confirm v0.1.9 boundary
  -> REL-10A formalize v0.1.10 scope
  -> UWBS-101
  -> UWBS-102
  -> UWBS-103
  -> UWBS-104
  -> REL-10C cumulative v0.1.10 acceptance
```

`v0.1.10` scope is fixed for planning as:

```text
UWBS-101..104 — Crypto On-chain Event Intelligence
```

## 4. v0.1.7–v0.1.9 release boundary work

These versions do not require reimplementation of already accepted features.

### v0.1.7

Scope:

```text
UWBS-080..086
Oil / Commodity / Cross-Asset
```

Action: confirm cumulative release boundary, ancestry/equivalence, acceptance evidence and manifest before any tag creation.

### v0.1.8

Scope:

```text
UWBS-087..093
Physical-SaaS
```

Action: confirm cumulative release boundary on top of v0.1.7, acceptance evidence and manifest before tag creation.

### v0.1.9

Scope:

```text
UWBS-094..100
VIX / Cross-Asset Volatility
```

Action: confirm cumulative release boundary on top of v0.1.8, acceptance evidence and manifest before tag creation.

## 5. v0.1.10 feature lane

### UWBS-101

Define cross-chain protocol wallet/component registry and confirmed on-chain transfer Fact contract.

Boundary:

- evidence-backed project / chain / wallet / contract roles;
- confirmed transfer event and accepted timestamps;
- tx hash, asset, amount, USD notional and provenance;
- unresolved relationships permitted;
- transfer facts never imply hack intent by themselves.

### UWBS-102

Implement abnormal on-chain flow Derived Metrics and candidate-state machine.

Dependency: `UWBS-101`.

Boundary:

- bounded 5m / 15m / 60m outflow observations;
- balance ratio and baseline ratio/z-score where valid;
- burst/destination metrics;
- candidate / confirmed anomaly interpretation states;
- alternative treasury / bridge-rebalance / unknown states remain representable.

### UWBS-103

Join on-chain anomaly candidates with market confirmation.

Dependencies:

```text
UWBS-102
UWBS-068..079 accepted crypto market-structure layer
```

Market context includes price, BTC-relative return, OI, funding, liquidations and available volume/CVD. Correlation must remain distinct from causal incident attribution.

### UWBS-104

Build historical exploit price-impact dataset and NEAR Intents replay fixture.

Dependencies:

```text
UWBS-101..103
UWBS-068..079 accepted market history / derivatives context
```

The fixture records first on-chain-detectable, first public and first official timestamps separately and computes event-window returns consistently rather than copying article-reported percentage declines.

## 6. Dependency view

```text
ACCEPTED CRYPTO FOUNDATION
UWBS-068..079
       |                  \
       |                   +-------> UWBS-104
       +-------> UWBS-103            ^
                    ^                 |
                    |                 |
UWBS-101 -> UWBS-102 ----------------+
                    |
                    +-------> UWBS-103 -> UWBS-104
```

Release ordering remains:

```text
v0.1.7 -> v0.1.8 -> v0.1.9 -> v0.1.10
```

## 7. PB lane

The market-dependent PB lane remains independent of this release/feature CP. No release-management action implicitly authorizes PB execution or live provider/runtime mutation.

## 8. Restart rule

After an interruption:

1. inspect `V0_1_7_TO_V0_1_10_RELEASE_CP_2026-10-02.md`;
2. resume at the first incomplete `REL-*` release gate;
3. do not repeat accepted UWBS-080..100 implementation;
4. after REL-09, start `UWBS-101` as the first new v0.1.10 implementation task;
5. continue sequentially through UWBS-104;
6. finish with REL-10C cumulative acceptance and tag-ready boundary definition.

Current selected restart:

```text
REL-07 — confirm v0.1.7 cumulative boundary
```
