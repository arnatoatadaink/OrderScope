# v0.1.6 UWBS-075 Implementation Progress — 2026-10-01

## Status

**Implementation complete / local acceptance validation pending**

UWBS-075 implements source-neutral liquidation normalization and deterministic cascade metrics on top of the accepted UWBS-074 archive/catch-up semantics.

## Scope

### CP-075A — Liquidation normalization

Implemented in `analysis/app/orderscope_local/crypto_derivatives/liquidations.py`.

- explicit `LiquidationSide` contract (`long` / `short`)
- explicit `LiquidationEvent` contract
- provider-specific buy/sell semantics are intentionally not inferred
- source fields are normalized only after the caller maps them to the liquidated-position side
- UTC and acceptance-time validation
- non-negative liquidation notional validation
- deterministic aggregation into the existing `LiquidationObservation` bucket contract
- half-open bucket interval `[bucket_start, bucket_end)`
- one venue/instrument series per bucket
- deterministic bucket identity from sorted event lineage
- long/short USD totals and event counts retained

### CP-075B — Cascade metrics

Implemented in `analysis/app/orderscope_local/crypto_derivatives/liquidation_metrics.py`.

Deterministic metrics only; no opaque composite risk score is introduced.

- `liquidation_total_usd`
- `liquidation_event_rate`
- `liquidation_acceleration_usd`
- `liquidation_multiplier`
- `liquidation_directional_share`

Pairwise cascade metrics require contiguous buckets from the same venue/instrument series. `liquidation_multiplier` rejects a zero previous total instead of inventing an infinite or sentinel value.

All UWBS-075 metrics use `method_version="uwbs-075-v1"` and preserve input observation IDs.

## Test coverage added

`analysis/tests/crypto_derivatives/test_liquidation_cascade.py`

Coverage includes:

- venue and side normalization
- invalid liquidated-side rejection
- negative notional rejection
- long/short/event-count aggregation
- deterministic bucket identity independent of input event order
- mixed-series rejection
- half-open bucket boundary rejection
- total, directional share, and event-rate metrics
- acceleration and multiplier over contiguous buckets
- non-contiguous bucket rejection
- zero-base multiplier rejection
- zero-notional directional-share behavior

## Branch / commits

Branch:

- `codex/uwbs-075-liquidation-cascade`

Accepted UWBS-074 base:

- `4c34a8f36f1083f84d46a788f62b9e7b05ad4adc`

Current UWBS-075 implementation head before this progress record:

- `6da880e9c630f69ea0c00626574011577a5ac769`

The implementation head is four commits ahead of the accepted UWBS-074 base and changes only:

- `analysis/app/orderscope_local/crypto_derivatives/__init__.py`
- `analysis/app/orderscope_local/crypto_derivatives/liquidation_metrics.py`
- `analysis/app/orderscope_local/crypto_derivatives/liquidations.py`
- `analysis/tests/crypto_derivatives/test_liquidation_cascade.py`

## Acceptance commands

Run locally:

```bash
uv run pytest -q analysis/tests/crypto_derivatives/test_liquidation_cascade.py
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

UWBS-075 should not be marked Accepted until these commands pass.
