# UWBS-097 Local Acceptance — 2026-09-28

Status: **ACCEPTED**

Task: **UWBS-097 — Implement BTC 30-day implied-volatility acquisition and normalization**

## Validation

Local WSL validation supplied by the operator:

```text
focused:          10 passed in 3.14s
full regression: 954 passed in 47.96s
compileall:       PASS
git diff --check: PASS
```

## Accepted boundary

- BTC 30-day implied-volatility observations are normalized with explicit provider/method lineage.
- The accepted representation preserves the exact 30-day horizon and converts annualized percent IV to a normalized fraction without turning IV into a directional BTC-price claim.
- Provider/method semantics remain explicit rather than being silently collapsed.
- No provider activation, paid procurement, Worker/Cron/D1 mutation, PB execution, or trading action is authorized by this acceptance.

## Result

UWBS-097 is accepted for merge to `main`.
