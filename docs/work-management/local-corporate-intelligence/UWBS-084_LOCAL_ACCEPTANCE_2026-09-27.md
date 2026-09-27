# UWBS-084 — Local Acceptance

Status: **ACCEPTED**
Date: 2026-09-27
Branch: `l1-003-local-market-recovery`

## Acceptance result

```text
BTC spot ETF flow contract:     7 passed
BTC spot ETF flow normalizer:   6 passed
full Python regression:       753 passed
compileall:                    PASS
git diff --check:              PASS
```

## Accepted boundary

UWBS-084 accepts the source-neutral BTC spot ETF flow boundary implemented on this branch:

- fund-level daily signed USD net-flow Facts are canonical;
- inflows remain positive and outflows remain negative;
- missing / unavailable source values are not coerced to zero;
- fund identity and observation date remain explicit;
- provider aggregate / TOTAL rows are not stored as canonical fund Facts;
- aggregate BTC spot ETF flow is a Derived Metric computed from fund-level Facts with lineage;
- ETF flow does not by itself establish BTC price causality, institutional conviction, or a Risk-On regime.

No live provider activation, Worker/Cron mutation, D1 mutation, paid procurement, or trading action was performed or authorized.

## Next dependency

Proceed to canonical `UWBS-085`:

`Define cross-asset Risk-On / Crypto Risk-On market-regime contract`.
