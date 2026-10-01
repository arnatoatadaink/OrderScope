# v0.1.6 UWBS-076 Implementation Progress — 2026-10-01

## Status

**Implementation complete / local acceptance validation pending**

UWBS-076 implements a deterministic Position Map / OI-retention estimate layer over aggregate crypto-derivatives observations.

## Interpretation boundary

Position Map is explicitly an inference layer. It does **not** claim exact trader-level entry prices or a true position ledger.

The model anchors positive open-interest growth to the contemporaneous price band and measures how much of that incremental OI remains at a later snapshot. Funding and subsequent liquidation totals are retained as contextual observations.

## CP-076A — Position Map

Implemented in:

- `analysis/app/orderscope_local/crypto_derivatives/position_map.py`

`PositionBandEstimate` retains:

- venue / instrument identity
- anchor price band
- baseline OI USD
- newly added OI USD
- retained OI USD
- OI retention ratio
- anchor funding rate
- subsequent long/short liquidation USD
- explicit input observation lineage
- `method_version="uwbs-076-v1"`

Default price-band width is 100 bps and is explicitly configurable.

## CP-076B — OI retention semantics

For ordered `baseline -> anchor -> as_of` observations:

```text
added = anchor_oi - baseline_oi
retained = min(added, max(as_of_oi - baseline_oi, 0))
retention_ratio = retained / added
```

The anchor must contain a positive OI increase. The retained estimate is capped at the original added OI so later unrelated OI growth is not retroactively attributed to the anchor band.

Subsequent liquidation context is included only when the liquidation bucket belongs to the same venue/instrument and falls within the anchor-to-as-of interval.

## Test coverage added

`analysis/tests/crypto_derivatives/test_position_map.py`

Coverage includes:

- partial OI retention
- full retention cap
- zero retention below baseline
- funding retention
- subsequent liquidation context
- cross-series liquidation exclusion
- non-positive anchor OI rejection
- mixed-series rejection
- missing OI rejection
- missing anchor price rejection
- invalid price-band width rejection

## Branch

- `codex/uwbs-076-position-map-oi-retention`

Accepted UWBS-075 base:

- `aece57aa74fd89e9ca975668c6f00817aa442d25`

## Acceptance commands

```bash
uv run pytest -q analysis/tests/crypto_derivatives/test_position_map.py
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

UWBS-076 remains pending until these commands pass locally.
