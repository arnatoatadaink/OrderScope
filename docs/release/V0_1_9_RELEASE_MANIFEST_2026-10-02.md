# OrderScope v0.1.9 Release Manifest — 2026-10-02

Status: **ACCEPTED / TAG READY**
Release: `v0.1.9`
Scope: `UWBS-094..100` — VIX / Cross-Asset Volatility

## Boundary

Accepted predecessor (`v0.1.8`):

```text
d34d471b20d4f5be865b0414a42240ec7f3061d9
```

Historical Physical-SaaS endpoint used to isolate the volatility delta:

```text
ae9f72b48a2b8e6a51bc2b2273969e7dc32d5325
```

Historical volatility endpoint:

```text
8151d1c2727fd22b0e9f0222f589cee666c99ffc
```

Validated reconstructed implementation candidate:

```text
530ae9087c53ced5f1c8261cf32d1e7687334943
```

The candidate is one commit ahead of the accepted reconstructed v0.1.8 boundary and contains exactly the 28 historical UWBS-094..100 volatility code/test/acceptance files. It introduces no UWBS-101..104 content and no deletion from the accepted predecessor tree.

## Exact-boundary validation

GitHub Actions run:

```text
36970709261
```

Validation result:

```text
Volatility focused tests:  82 passed
Full Python regression:  1097 passed
Python compileall:          PASS
Worker tests:               227 passed / 0 failed
Worker typecheck:           PASS
git diff --check:           PASS
```

The workflow checked out exact SHA `530ae9087c53ced5f1c8261cf32d1e7687334943` before executing the gates.

## Semantic boundary

`v0.1.9` preserves volatility observations and derived metrics as evidence. VIX level/change, futures term structure, ETP roll/decay, BTC IV30, MSTR IV30, MSTR/BTC IV differential, and calibration outputs do not by themselves authorize a directional trading conclusion or production action.

No live-provider activation, Worker/Cron mutation, D1 mutation, PB execution, automated trading action, or UWBS-101..104 on-chain security implementation is introduced by this release reconstruction.

## Decision

```text
Accepted v0.1.8 predecessor       PASS
UWBS-094..100 historical delta    PASS
28-file reconstruction            PASS
Later-feature exclusion           PASS
Exact-boundary CI                 PASS
Manifest                          COMPLETE
REL-09                            ACCEPTED
Tag readiness                     READY
```

Annotated tag creation may target the documentation-complete descendant of the validated candidate after the REL-09 acceptance record is committed. Published `main` history is not rewritten.
