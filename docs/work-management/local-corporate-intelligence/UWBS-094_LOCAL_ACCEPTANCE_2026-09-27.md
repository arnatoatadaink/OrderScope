# UWBS-094 Local Acceptance — Volatility Benchmark Fact Contract

Status: **ACCEPTED**
Date: 2026-09-27
Scope: repository-backed / local deterministic contract boundary

## Verification

```text
focused volatility benchmark tests: 10 passed in 1.75s
full Python regression:            914 passed in 33.80s
compileall:                        PASS
git diff --check:                 PASS
```

## Accepted boundary

UWBS-094 keeps these instrument classes distinct at the Fact layer:

- published volatility index;
- volatility future;
- VIX-linked ETP proxy.

A published volatility index is not treated as a directly tradable currency-priced instrument. Futures require explicit maturity. ETP proxies use market-price / currency semantics and must not be represented as volatility-index points.

This acceptance does not infer contango, backwardation, roll yield, fear regime, or cross-asset causality. Those remain downstream DerivedMetric / Interpretation work.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this acceptance.
