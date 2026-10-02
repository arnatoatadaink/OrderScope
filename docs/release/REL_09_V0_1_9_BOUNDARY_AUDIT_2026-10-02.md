# REL-09 — v0.1.9 Boundary Audit — 2026-10-02

Status: **RECONSTRUCTION IN PROGRESS — HISTORICAL UWBS-094..100 DELTA VERIFIED**
Release target: `v0.1.9`
Scope: `UWBS-094..100` VIX / Cross-Asset Volatility

## 1. Accepted predecessor

Accepted reconstructed v0.1.8 boundary:

```text
d34d471b20d4f5be865b0414a42240ec7f3061d9
Accept REL-08 v0.1.8 boundary
```

REL-09 reconstruction must preserve this cumulative predecessor unchanged.

## 2. Historical v0.1.9 endpoint

Historical UWBS-094..100 endpoint:

```text
8151d1c2727fd22b0e9f0222f589cee666c99ffc
Accept UWBS-100 volatility calibration
```

Historical predecessor used to isolate the v0.1.9 feature delta:

```text
ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325
```

GitHub comparison result:

```text
base:      ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325
head:      8151d1c2727fd22b0e9f0222f589cee666c99ffc
status:    ahead
ahead_by:  39
behind_by: 0
```

The isolated file delta is 28 files and contains only the UWBS-094..100 volatility lane:

- volatility benchmark contract
- VIX term structure
- VIX ETP roll boundary
- VIX level/change/curve interpretation
- BTC IV30 normalization
- MSTR IV30 normalization
- MSTR/BTC IV30 differential
- volatility historical calibration
- corresponding focused tests
- UWBS-094..100 acceptance/design evidence

No UWBS-101..104 Crypto On-chain Event Intelligence content appears in this historical delta.

## 3. Reconstruction decision

Do not tag the historical `8151d1c...` commit directly as cumulative v0.1.9 because the accepted predecessor is now the reconstructed v0.1.8 boundary `d34d471...`.

Selected method:

```text
accepted reconstructed v0.1.8
  d34d471b20d4f5be865b0414a42240ec7f3061d9
        +
historical-only UWBS-094..100 delta
  ae9f72b... -> 8151d1c...
        =
reconstructed cumulative v0.1.9 candidate
```

Staging branch:

```text
release/reconstructed-v0.1.9
base: d34d471b20d4f5be865b0414a42240ec7f3061d9
```

## 4. Semantic boundaries to preserve

- VIX / IV / term-structure observations are volatility evidence, not automatic directional predictions.
- MSTR/BTC IV differentials remain descriptive/derived metrics unless a separately accepted interpretation rule exists.
- Historical calibration must not silently become a live trading rule.
- No provider activation, Worker/Cron mutation, D1 mutation, PB authorization, automated trading action, or UWBS-101..104 implementation is authorized by REL-09.

## 5. REL-09 gate state

```text
REL-08 predecessor accepted:                 PASS
Historical UWBS-094..100 endpoint identified: PASS
Historical feature delta isolated:           PASS
Later UWBS-101..104 exclusion:                PASS
Reconstruction branch created:                PASS
Cumulative v0.1.9 candidate tree:              PENDING
Focused volatility tests:                      PENDING
Full Python regression:                        PENDING
Worker tests/typecheck:                        PENDING
compileall / git diff --check:                  PENDING
v0.1.9 manifest:                                PENDING
REL-09 acceptance:                              PENDING
Tag readiness:                                  NOT READY
```

## 6. Next step

Apply the isolated 28-file UWBS-094..100 delta to `release/reconstructed-v0.1.9`, then validate the exact reconstructed candidate and write `V0_1_9_RELEASE_MANIFEST_2026-10-02.md`.
