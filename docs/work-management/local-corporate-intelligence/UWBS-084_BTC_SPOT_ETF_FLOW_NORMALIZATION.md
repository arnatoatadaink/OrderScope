# UWBS-084 — BTC Spot ETF Flow Acquisition / Normalization

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Canonical task: `UWBS-084`
Dependency: `UWBS-070` institutional-flow source survey

## Objective

Normalize externally reported U.S. spot-Bitcoin ETF daily fund flows without treating flow as a price-causality or Risk-On conclusion.

## Canonical truth boundary

The source-grounded Fact is one fund / one date / one signed net flow:

```text
fund_ref
ticker
flow_date
net_flow_usd
provenance
```

Positive values are inflows, negative values are outflows, zero is a valid observed zero. Missing/withheld/non-numeric provider markers are not converted to zero.

## Aggregate rule

Provider `TOTAL` / `ALL` / aggregate rows are not canonical fund Facts. Market-wide BTC spot ETF flow is a `DerivedMetric` calculated from unique normalized fund-level Facts for the same date.

This preserves lineage and prevents double counting or silent dependence on provider total methodology.

## Explicit exclusions

UWBS-084 does not infer:

- BTC price direction;
- institutional conviction;
- Risk-On / Risk-Off state;
- ETF-flow causality;
- weekend/weekday market regime;
- derivatives positioning.

Those remain downstream of the normalized flow observations.

## Acquisition boundary

`BtcSpotEtfFundProfile` maps one provider fund identifier to one canonical fund reference and ticker. `normalize_btc_spot_etf_flow_row()` accepts a provider row only when:

- the fund identity matches the configured profile;
- date is canonical ISO date / date object;
- flow is finite numeric USD;
- missing markers are rejected rather than imputed.

The implementation is provider-neutral and does not activate a live source or paid provider.

## Acceptance commands

```bash
uv run pytest -q analysis/tests/contracts/test_crypto_etf_flow.py
uv run pytest -q analysis/tests/crypto/test_btc_spot_etf_flow.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

Focused test count: 13.

No Worker/Cron mutation, D1 mutation, live provider activation, PB authorization, paid procurement, or trading action is authorized by this task.
