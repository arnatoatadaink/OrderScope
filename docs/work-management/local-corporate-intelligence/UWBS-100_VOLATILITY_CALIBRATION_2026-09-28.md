# UWBS-100 — Volatility Historical Calibration and Canary Evaluation

Status: **ACCEPTED**

Date: 2026-09-28

## Purpose

Close the current UWBS volatility-analysis series with a bounded historical calibration lane built on the accepted UWBS-094..099 contracts. UWBS-100 compares candidate alert rules against historical windows and separately checks Worker/D1 capacity evidence. It does not activate a live rule.

## Dependencies

- UWBS-096 volatility ETP roll boundary: ACCEPTED upstream dependency.
- UWBS-097 BTC IV30 normalization: ACCEPTED upstream dependency.
- UWBS-098 MSTR IV30 normalization: ACCEPTED upstream dependency.
- UWBS-099 MSTR/BTC IV30 differential: ACCEPTED upstream dependency.
- UWBS-086 historical Canary / Worker-D1 capacity contracts are reused for infrastructure-capacity assessment.

## Implemented scope

### Historical windows

The calibration contract explicitly supports:

- `CALM`
- `CORRECTION`
- `SHOCK`
- `RECOVERY`
- `MSTR_BTC_DIVERGENCE`
- `CONTROL`

A suite reports whether all required window kinds are covered, but incomplete suites remain representable so partial research evidence can be inspected without pretending to be complete.

### Candidate rule families

UWBS-100 compares three bounded candidate rule families:

1. `ABSOLUTE_THRESHOLD`
2. `EMPIRICAL_PERCENTILE`
3. `Z_SCORE`

The module evaluates candidates only. No candidate becomes a production rule, deployment threshold, trading signal, or Regime transition.

### Canary-quality evidence

Each candidate evaluation records:

- true positives
- false positives
- true negatives
- false negatives
- total classification errors
- precision where defined
- recall where defined

This allows false-positive and false-negative comparison without promoting a chosen threshold into a normative production setting.

### Lead / lag evidence

When a historical point carries an explicit event timestamp and the rule alerts, timing is measured as:

`observed_at - event_at`

Therefore:

- negative seconds = alert observation precedes the event timestamp (lead)
- zero = coincident
- positive seconds = alert observation follows the event timestamp (lag)

Timing is evidence only and is not interpreted as causality.

### Capacity boundary

UWBS-100 does not duplicate Cloudflare capacity arithmetic. It consumes the accepted UWBS-086 `ProjectedCapacityUsage` and `CapacityEnvelope` contracts and delegates headroom calculation to `build_capacity_observation`.

Classification quality and capacity remain independent acceptance dimensions: a historically clean rule can still fail capacity headroom, and sufficient capacity cannot repair poor historical classification.

## Files

- `analysis/app/orderscope_local/cross_market/volatility_calibration.py`
- `analysis/tests/cross_market/test_volatility_calibration.py`
- `docs/work-management/local-corporate-intelligence/UWBS-100_VOLATILITY_CALIBRATION_2026-09-28.md`

## Non-goals

UWBS-100 does **not**:

- activate a production threshold
- change Worker/Cron cadence
- mutate D1
- call Cloudflare, Alpaca, options providers, or paid APIs
- infer market direction from volatility alone
- infer causality from lead/lag timing
- infer MSTR leverage, NAV premium, dealer gamma, positioning, or volatility risk premium
- create a trading recommendation
- alter PB-04..PB-10 state or authorization

## Local acceptance evidence

Validated on 2026-09-28:

```text
uv run pytest -q analysis/tests/cross_market/test_volatility_calibration.py
13 passed in 2.60s

uv run pytest -q analysis/tests
986 passed in 42.82s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no error output)
```

## Acceptance result

`ACCEPTED`

UWBS-100 satisfies the bounded local acceptance target. The implementation keeps production-rule activation and live infrastructure mutation outside this task.

## Closure rule

UWBS-094..100 are accepted for this iteration and the current UWBS volatility series is closed. PB work remains a separate lane and must be closed only through its own market-session validation and authorization gates.
