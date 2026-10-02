# UWBS-094 — Volatility Benchmark Observation Contract

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

## Purpose

Define a source-neutral Fact boundary for volatility observations while keeping a published volatility index, volatility future, and exchange-traded proxy distinct.

## Contract boundary

Accepted raw observation classes:

- published volatility index level;
- implied-volatility index level;
- volatility future settlement/close/market price with explicit maturity;
- ETP proxy NAV/market price/close with explicit currency.

The contract intentionally prevents the following category errors:

- a VIX-linked ETF/ETN is not the VIX index;
- a volatility future is not a spot/index level and must carry maturity;
- an index level is not a currency-denominated asset price;
- an ETP price is not measured in volatility points;
- futures/ETP observations do not by themselves establish contango, backwardation, roll yield, fear regime, or directional market risk.

## Fact / DerivedMetric / Interpretation split

UWBS-094 records only source-observed instrument values as Facts. Term-structure spreads, roll/contango measurements and regime conclusions belong to later DerivedMetric / Interpretation tasks.

## Implementation

```text
analysis/app/orderscope_local/contracts/volatility_benchmark.py
analysis/tests/contracts/test_volatility_benchmark.py
```

## Runtime boundary

No provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this task.
