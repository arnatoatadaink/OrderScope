# UWBS-097 — BTC 30-Day Implied-Volatility Acquisition / Normalization

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**
Canonical task: implement BTC 30-day implied-volatility acquisition and normalization.

## Boundary

UWBS-097 normalizes a source observation to annualized 30-day BTC implied volatility while keeping provider/methodology identity explicit.

Accepted source-method classes:

- published implied-volatility index;
- ATM option-surface estimate;
- delta-neutral composite.

Normalized representation:

```text
annualized_iv_percent
normalized_fraction = annualized_iv_percent / 100
horizon_days = 30
underlying_ref = crypto.btc
```

The observation is a Fact. It does not infer BTC price direction, Risk-On/Risk-Off state, positioning, liquidation risk, or MSTR relative volatility.

## Guards

- non-BTC underlying is rejected;
- horizon must be exactly 30 days;
- IV must be finite non-negative Decimal;
- UTC observation/acceptance times are required;
- acceptance and provenance timestamps must remain consistent;
- evidence lineage is mandatory when materializing the Fact.

## Runtime boundary

This implementation does not activate a provider, paid API, Worker/Cron job, D1 mutation, PB execution, or trading action. Provider selection/activation remains a separate operational decision.
