# UWBS-085 — Cross-Asset Risk-On / Crypto Risk-On Regime

Status: **WEB IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Branch: `l1-003-local-market-recovery`

## Purpose

Define an Interpretation-layer regime contract that distinguishes broad cross-asset Risk-On from crypto-specific Risk-On without treating one BTC move, one ETF-flow print, or one commodity signal as sufficient evidence.

## Regime types

- `broad_risk_on`
- `crypto_risk_on`
- `risk_off`
- `divergent`

Each regime is assessed with `SUPPORT`, `PARTIAL`, `CONTRADICT`, or `UNKNOWN`.

## Independent signal classes

The assessment preserves separate references for:

1. traditional risk-asset metrics;
2. crypto market metrics;
3. crypto derivatives metrics;
4. BTC spot ETF-flow metrics from UWBS-084;
5. macro / commodity interpretations including UWBS-083;
6. volatility metrics;
7. contradicting evidence.

References cannot be reused across signal classes.

## Evidence rules

`SUPPORT` requires at least three independent supporting classes. `PARTIAL` requires at least two.

Additional semantic guards:

- `broad_risk_on` requires traditional risk-asset evidence and cross-asset confirmation;
- `crypto_risk_on` requires crypto market evidence plus ETF-flow or derivatives confirmation;
- `risk_off` requires traditional-risk or volatility evidence;
- `divergent` requires both traditional and crypto evidence;
- `UNKNOWN` carries no directional evidence;
- `CONTRADICT` requires explicit contradicting evidence.

The design deliberately prevents `BTC up -> Risk-On` and `ETF inflow -> institutional bullish regime` shortcuts.

## Downstream boundary

UWBS-085 creates a regime Interpretation with complete basis lineage. It does not execute trades, change universe membership, mutate Worker/Cron/D1 runtime, or activate providers.

## Acceptance

Run:

```bash
uv run pytest -q analysis/tests/contracts/test_cross_asset_regime.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

If accepted, add the shared contract export, record local acceptance, then proceed to UWBS-086 historical Canary + Worker/D1 capacity acceptance.
