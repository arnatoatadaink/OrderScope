# UWBS-086 — 2024-08-05 Historical Replay Packet Local Acceptance — 2026-09-27

Status: **ACCEPTED — PACKET CONSTRUCTION / MANIFEST LOADER**
Branch: `l1-003-local-market-recovery`

## Accepted artifact

Historical packet:

`analysis/config/cross_market/uwbs-086-2024-08-05-risk-off-v0.1.json`

Window:

```text
2024-08-02T00:00:00Z .. 2024-08-08T00:00:00Z
```

Expected label is independently evidenced as:

```text
regime: risk_off
alert:  true
```

The expected-label evidence is separate from classifier-input evidence.

## Required lanes

All nine required historical replay lanes are present exactly once:

```text
oil_price
commodity_fundamental
commodity_event
commodity_interpretation
btc_spot_etf_flow
traditional_risk
crypto_market
crypto_derivatives
volatility
```

## Local verification

User-reported local acceptance result on 2026-09-27:

```text
historical replay packet contract:   9 passed
historical replay manifest:          9 passed
full Python regression:            799 passed
compileall:                         PASS
git diff --check:                   PASS
```

## Boundary

This acceptance proves packet completeness, manifest validation, repository-backed source identity and expected-label separation. It does not yet prove the observed regime because the historical replay runner is a separate step.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution or trading action was performed.
