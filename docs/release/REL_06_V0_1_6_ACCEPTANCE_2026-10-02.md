# REL-06 — v0.1.6 exact-boundary acceptance — 2026-10-02

Status: **ACCEPTED / TAG READY**

## Boundary

```text
bfaf89c68daa656b7d75317f086458257cc94da9
Reflect accepted v0.1.6 WBS and CP progress
```

This boundary is the resolved cumulative successor of accepted v0.1.5 boundary `415de1f1dd42f70bd66992961cb43be7edba6ade`.

Lineage review established that `bfaf89c...` is 56 commits ahead / 0 behind from v0.1.5, with the v0.1.5 boundary itself as merge base. The delta is confined to the canonical v0.1.6 crypto lane, its tests, and v0.1.6 release documentation.

## Exact-boundary validation

User-executed commands on detached HEAD at the exact release SHA:

```text
git switch --detach bfaf89c68daa656b7d75317f086458257cc94da9
git rev-parse HEAD
git status --short
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
npm test
npm run typecheck
```

Observed results:

```text
HEAD                    bfaf89c68daa656b7d75317f086458257cc94da9
working tree            clean
Python analysis tests   746 passed, 1 warning
Worker tests            178 passed / 0 failed
compileall              PASS
git diff --check        PASS
TypeScript typecheck    PASS
```

The Python warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not a release blocker.

## Scope

v0.1.6 contains the canonical Crypto Market Structure lane:

- UWBS-068 Crypto derivatives Fact / Derived Metric contract
- UWBS-069 BTC macro-leader / altcoin relative-context model
- UWBS-070 institutional-flow / market-structure source survey
- UWBS-071 24/7 crypto time-window / weekend-liquidity contract
- UWBS-072 NEAR/BTC multi-layer Canary
- UWBS-073 multi-venue futures/perpetual adapters
- UWBS-074 durable derivatives snapshot archive / catch-up lifecycle
- UWBS-075 liquidation normalization / cascade metrics
- UWBS-076 price-zone OI retention / Position Map
- UWBS-077 cross-venue divergence / data-quality guards
- UWBS-078 futures-position NEAR Canary
- UWBS-079 Stage A weekend handoff / weekday re-risking implementation

UWBS-079 Stage B empirical multi-week recurrence validation remains `PENDING / EXPERIMENTAL` and is explicitly non-blocking for this development release.

## Decision

```text
boundary lineage                  PASS
scope isolation                   PASS
historical CP-16X acceptance      PASS
exact-boundary Python regression  PASS
exact-boundary Worker regression  PASS
compile/type/diff gates           PASS
release classification            ACCEPTED / TAG READY
```

This record does not create a Git tag and does not authorize live provider or production mutation changes.
