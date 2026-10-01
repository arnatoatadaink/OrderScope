# v0.1.6 UWBS-079 Stage A Acceptance — 2026-10-01

## Status

**Stage A Accepted / multi-week empirical validation still pending**

UWBS-079 closes the implementation and regression-test portion of the Pacific weekend handoff / weekday re-risking validation task.

This acceptance does **not** claim that the weekend-to-weekday re-risking hypothesis is empirically validated or recurrent. That requires a separate multi-week sample.

## Accepted Stage A scope

- deterministic weekend handoff validation model
- independent-week sample accounting
- BTC return by weekend window
- altcoin return by weekend window
- synchronized breadth
- BTC→altcoin lag observation
- spot volume change
- derivatives volume change
- OI change
- funding change
- liquidation imbalance
- 1h / 3h / 6h / 24h persistence
- multi-week summary statistics
- explicit `INSUFFICIENT_SAMPLE` vs `EXPERIMENTAL` status boundary
- no participant-nationality inference
- no causal claim from timing/correlation alone

## Acceptance evidence

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_canary/test_weekend_validation.py
10 passed in 2.20s

uv run pytest -q analysis/tests/crypto_canary
20 passed in 1.90s

uv run pytest -q analysis/tests
746 passed, 1 warning in 43.26s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not a UWBS-079 Stage A acceptance blocker.

## Remaining Stage B requirement

UWBS-079 empirical recurrence remains pending until multiple independent weekends are collected and evaluated, including at minimum materially different regimes such as:

- broad crypto risk-on weekend
- risk-off weekend
- BTC-flat weekend
- target-specific catalyst weekend
- no-material-event control weekend

The multi-week result may remain **EXPERIMENTAL** for v0.1.6; it must not be presented as validated causal recurrence without evidence.

## Handoff

Proceed to `CP-16X` for the v0.1.6 boundary-level regression and release acceptance review while tracking UWBS-079 Stage B as an experimental empirical-validation follow-up.
