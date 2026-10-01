# v0.1.6 UWBS-078 Implementation Progress — 2026-10-01

## Status

**Implementation complete / local acceptance validation pending**

UWBS-078 implements the NEAR futures-position Canary by composing accepted crypto-derivatives layers from UWBS-075 through UWBS-077.

## Interpretation boundary

The Canary is descriptive monitoring and QA context only. It does not:

- predict price direction
- emit buy/sell recommendations
- identify traders
- claim an exact position ledger
- treat any venue or median as ground truth
- produce an opaque composite score

## Inputs

The Canary consumes already-normalized NEAR derivatives observations and optional:

- UWBS-076 Position Map estimates
- UWBS-075 liquidation buckets
- UWBS-077 cross-venue diagnostics

## Outputs

`NearFuturesPositionCanary` contains:

- instrument / as-of time
- venue count
- median open-interest USD
- median funding rate
- median mark price
- maximum relative OI deviation across venues
- maximum absolute funding-rate deviation across venues
- maximum relative mark-price deviation across venues
- weighted Position Map OI-retention ratio
- aggregate long-liquidation USD
- aggregate short-liquidation USD
- liquidation directional share
- deterministic QA flags
- explicit immutable input lineage
- `method_version="uwbs-078-v1"`

## QA flags

Initial deterministic QA thresholds:

- OI relative deviation: `0.15`
- funding absolute deviation: `0.001`
- mark-price relative deviation: `0.01`
- Position Map retention ratio: `0.50`

These are review thresholds, not market-direction signals. All are explicit function arguments and can be recalibrated later without changing the observation contract.

Possible flags:

- `oi_cross_venue_mismatch`
- `funding_cross_venue_mismatch`
- `mark_cross_venue_mismatch`
- `position_retention_below_threshold`

## Test coverage added

`analysis/tests/crypto_derivatives/test_near_futures_canary.py`

Coverage includes:

- cross-venue OI/funding/mark composition
- weighted OI-retention calculation
- liquidation directional aggregation
- deterministic QA flags
- non-NEAR rejection
- Position Map instrument mismatch rejection
- liquidation instrument mismatch rejection
- invalid retention threshold rejection
- minimum two-venue requirement
- stable deduplicated lineage

## Branch

- `codex/uwbs-078-near-futures-position-canary`

Accepted UWBS-077 base:

- `1348ff64520fee5f0215591a985b36b6fb66e8e8`

## Acceptance commands

```bash
uv run pytest -q analysis/tests/crypto_derivatives/test_near_futures_canary.py
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

UWBS-078 remains pending until these commands pass locally.
