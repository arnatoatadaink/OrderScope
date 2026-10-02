# REL-09 — v0.1.9 Boundary Audit — 2026-10-02

Status: **ACCEPTED / TAG READY**
Release target: `v0.1.9`
Scope: `UWBS-094..100` — VIX / Cross-Asset Volatility

## 1. Decision summary

The historical v0.1.9 feature-lane endpoint is:

```text
8151d1c2727fd22b0e9f0222f589cee666c99ffc
Accept UWBS-100 volatility calibration
```

Because the accepted `v0.1.8` release was reconstructed after the historical feature-lane closeout, the historical endpoint cannot be tagged directly as the cumulative `v0.1.9` release.

REL-09 therefore reconstructs only the historical volatility delta from:

```text
ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325
  ->
8151d1c2727fd22b0e9f0222f589cee666c99ffc
```

onto the accepted reconstructed v0.1.8 boundary:

```text
d34d471b20d4f5be865b0414a42240ec7f3061d9
```

Validated implementation candidate:

```text
530ae9087c53ced5f1c8261cf32d1e7687334943
```

## 2. Historical delta audit

The historical `ae9f72... -> 8151d1c...` comparison is 39 commits ahead / 0 behind and yields exactly 28 files belonging to UWBS-094..100 volatility work.

The reconstructed candidate is:

```text
base:      d34d471b20d4f5be865b0414a42240ec7f3061d9
head:      530ae9087c53ced5f1c8261cf32d1e7687334943
status:    ahead
ahead_by:  1
behind_by: 0
```

Its delta is exactly those same 28 volatility files, with no deletions.

## 3. Scope boundary

Included:

- UWBS-094 volatility benchmark observation contract
- UWBS-095 volatility futures term structure
- UWBS-096 VIX level/change/curve interpretation and ETP roll boundary
- UWBS-097 BTC IV30 normalization
- UWBS-098 MSTR IV30 normalization
- UWBS-099 MSTR/BTC IV30 differential
- UWBS-100 historical volatility calibration / Canary evaluation

Excluded:

- UWBS-101..104 Crypto On-chain Event Intelligence
- new provider activation
- Worker/Cron production mutation
- D1 mutation-policy changes
- PB authorization changes
- automated trading behavior

Volatility evidence remains separated from automatic directional interpretation.

## 4. Exact-boundary validation

GitHub Actions run:

```text
36970709261
```

The workflow explicitly checked out candidate SHA `530ae9087c53ced5f1c8261cf32d1e7687334943`.

Results:

```text
Volatility focused tests:  82 passed
Full Python regression:  1097 passed
Python compileall:          PASS
Worker tests:               227 passed / 0 failed
Worker typecheck:           PASS
git diff --check:           PASS
```

## 5. REL-09 gate state

```text
Accepted v0.1.8 predecessor:       PASS
Historical UWBS-094..100 endpoint: PASS
Historical delta isolation:        PASS
Cumulative reconstruction:         PASS
Later-feature exclusion:           PASS
Exact-boundary CI:                 PASS
v0.1.9 manifest:                   COMPLETE
REL-09:                            ACCEPTED
v0.1.9 tag readiness:              READY
```

## 6. Release boundary

Implementation validation authority remains candidate:

```text
530ae9087c53ced5f1c8261cf32d1e7687334943
```

Subsequent commits on `release/reconstructed-v0.1.9` are release-documentation-only. The branch HEAD after this acceptance record is the documentation-complete tag-ready descendant.

Next critical-path stage:

```text
REL-10A — formalize v0.1.10 scope
v0.1.10 = UWBS-101..104
```
