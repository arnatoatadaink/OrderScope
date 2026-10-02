# UWBS-099 — MSTR/BTC 30-day IV differential

Status: **ACCEPTED**

## Scope

UWBS-099 defines the deterministic comparison boundary between the accepted
UWBS-097 BTC IV30 observation and UWBS-098 MSTR IV30 observation.

The comparison is stored as a `DerivedMetric`, not a new source observation.

## Accepted calculation boundary

The metric records:

- MSTR annualized 30-day IV percent;
- BTC annualized 30-day IV percent;
- `MSTR IV - BTC IV` in percentage points;
- the equivalent normalized fractional differential;
- both source observation timestamps;
- `as_of` equal to the later source observation timestamp;
- exactly two distinct input record ids for calculation lineage.

No synchronization tolerance is assumed. UWBS-099 preserves both source
timestamps instead of deciding that observations within an arbitrary time
window are equivalent.

## Sign convention

```text
positive differential = MSTR IV > BTC IV
zero differential     = MSTR IV = BTC IV
negative differential = MSTR IV < BTC IV
```

The sign is arithmetic only and is not a market-direction or regime signal.

## Acceptance evidence

Local acceptance completed on 2026-09-28 JST.

```text
uv run pytest -q analysis/tests/cross_market/test_mstr_btc_iv30.py
9 passed

uv run pytest -q analysis/tests
973 passed

uv run python -m compileall -q analysis/app
no error output

git diff --check
no error output
```

## Non-goals

UWBS-099 does not infer:

- MSTR or BTC price direction;
- causal linkage between BTC and MSTR volatility;
- MSTR embedded leverage or NAV premium;
- volatility risk premium;
- option positioning or dealer gamma;
- Risk-On / Risk-Off regime;
- a trading action or alert threshold.

Those require separately specified downstream interpretation boundaries.

No provider activation, paid procurement, Worker/Cron/D1 mutation, PB
execution, or trading action is authorized by this implementation.
