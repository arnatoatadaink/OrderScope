# v0.1.6 UWBS-077 Implementation Progress — 2026-10-01

## Status

**Implementation complete / local acceptance validation pending**

UWBS-077 adds a deterministic cross-venue QA layer over normalized crypto-derivatives observations.

## Scope boundary

UWBS-077 does not declare any venue authoritative and does not infer manipulation, trader intent, or directional capital flow. It only determines whether observations are comparable and emits descriptive mismatch diagnostics.

## CP-077A — Comparable snapshot grouping

Implemented in:

- `analysis/app/orderscope_local/crypto_derivatives/cross_venue_qa.py`

Rules:

- at least two observations
- same `instrument_id`
- same `contract_type`
- unique venue per comparison group
- bounded observation-time skew
- deterministic venue/time/id ordering

Default maximum time skew is 60 seconds and is configurable.

## CP-077B — Deterministic mismatch diagnostics

Implemented diagnostics:

- `diagnose_open_interest_usd`
- `diagnose_funding_rate`
- `diagnose_mark_price`

Each diagnostic retains:

- instrument identity
- deterministic `as_of`
- metric name / unit
- venue/value pairs
- cross-venue median
- maximum absolute deviation from the median
- maximum relative deviation when the median is non-zero
- input observation lineage
- `method_version="uwbs-077-v1"`

The median is used as a descriptive center only; it is not treated as ground truth.

## Test coverage added

`analysis/tests/crypto_derivatives/test_cross_venue_qa.py`

Coverage includes:

- deterministic venue ordering
- mixed-instrument rejection
- duplicate-venue rejection
- time-skew rejection
- OI median/deviation/lineage
- negative and zero funding values
- mark-price relative deviation
- missing metric rejection
- insufficient observation count rejection
- invalid skew argument rejection

## Branch

- `codex/uwbs-077-cross-venue-qa`

Accepted UWBS-076 base:

- `a0cfe87e2f22fd470b97ca218959ef45eb668128`

## Acceptance commands

```bash
uv run pytest -q analysis/tests/crypto_derivatives/test_cross_venue_qa.py
uv run pytest -q analysis/tests/crypto_derivatives
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

UWBS-077 remains pending until these commands pass locally.
