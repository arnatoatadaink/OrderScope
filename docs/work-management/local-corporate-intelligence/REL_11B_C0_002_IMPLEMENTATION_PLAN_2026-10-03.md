# OrderScope — REL-11B / C0-002 Implementation Plan — 2026-10-03

Status: **IMPLEMENTATION PLAN — REL-11B START**
Release: `v0.1.11`
Formal WBS: `C0-002`
Canonical source: `UWBS-107`
Upstream accepted dependency: `REL-11A / C0-001 / UWBS-106`

## 1. Goal

Implement deterministic abnormal on-chain flow Derived Metrics and a bounded candidate-state model over accepted C0-001 confirmed-transfer Facts.

## 2. Package boundary

Extend:

`analysis/app/orderscope_local/crypto_onchain/`

REL-11B module:

- `flow_metrics.py` — fixed-window outflow aggregation, baseline/balance ratios, z-score when valid, burst/destination metrics, candidate state, and alternative-explanation preservation.

Focused tests:

`analysis/tests/crypto_onchain/test_c0_002_flow_metrics.py`

## 3. Metric boundary

Initial deterministic windows:

- 5 minutes;
- 15 minutes;
- 60 minutes.

For a monitored address and accepted as-of time, compute only confirmed transfers available no later than as-of.

Metrics include:

- outbound USD notional by window where USD notional exists;
- outbound transfer count;
- distinct destination count;
- known/unknown destination-class counts;
- ratio to supplied current balance when valid;
- ratio to supplied historical baseline mean when valid;
- z-score when baseline mean and positive standard deviation are valid.

Missing required baseline data remains `None` / `UNKNOWN`; it must not be fabricated.

## 4. Candidate-state boundary

Candidate states are interpretation labels only:

- `UNKNOWN` — insufficient eligible baseline/context;
- `NORMAL` — eligible metrics exist and thresholds are not reached;
- `ELEVATED` — bounded intermediate anomaly signal;
- `ABNORMAL_FLOW_CANDIDATE` — high bounded anomaly signal.

No state means exploit, theft, malicious activity, or confirmed security incident.

## 5. Alternative explanations

Candidate output preserves zero or more explicit alternatives independently of severity:

- `TREASURY_MOVEMENT`;
- `BRIDGE_REBALANCE`;
- `UNKNOWN`.

Alternative explanations are evidence/context supplied to the metric layer; they do not silently suppress an abnormal-flow candidate.

## 6. Initial thresholds

Thresholds are explicit configuration, not hidden constants. Default fixture thresholds:

- elevated: baseline ratio >= 2.0 or z-score >= 2.0 or balance ratio >= 0.10;
- abnormal candidate: baseline ratio >= 3.0 or z-score >= 3.0 or balance ratio >= 0.25;
- burst count threshold is configurable and contributes only when a valid amount/baseline signal also exists.

These defaults are deterministic test/initial-analysis parameters, not empirical production calibration.

## 7. Acceptance scope

Focused tests must cover:

1. exact 5m/15m/60m windows;
2. no-lookahead via `available_at <= as_of`;
3. outbound direction only for the monitored address;
4. missing USD notional handling;
5. balance/baseline ratio calculation;
6. z-score only with valid positive standard deviation;
7. burst and distinct-destination metrics;
8. `UNKNOWN` when evidence is insufficient;
9. deterministic NORMAL/ELEVATED/ABNORMAL candidate transitions;
10. treasury/bridge/unknown alternatives retained separately from severity;
11. no incident-attribution fields or state.

Before REL-11B acceptance run:

```bash
uv run pytest -q analysis/tests/crypto_onchain/test_c0_001_registry.py \
  analysis/tests/crypto_onchain/test_c0_002_flow_metrics.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

## 8. Non-goals

REL-11B does not add provider adapters, mempool monitoring, market price/OI/funding/liquidation joins, exploit attribution, Worker/Cron/D1 mutation, or automated trading.
