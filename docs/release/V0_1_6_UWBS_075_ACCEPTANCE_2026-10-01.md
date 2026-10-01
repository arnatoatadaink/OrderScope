# v0.1.6 UWBS-075 Acceptance — 2026-10-01

## Status

**Accepted**

UWBS-075 closes the source-neutral liquidation normalization and deterministic cascade-metric layer.

## Accepted scope

### CP-075A — Liquidation normalization

- explicit liquidated-position side contract (`long` / `short`)
- source-neutral liquidation event contract
- UTC / acceptance-time validation
- non-negative liquidation notional validation
- deterministic bucket aggregation
- half-open bucket semantics `[bucket_start, bucket_end)`
- single venue/instrument series enforcement
- deterministic bucket identity from sorted event lineage
- long/short liquidation USD totals and event counts retained

### CP-075B — Cascade metrics

- `liquidation_total_usd`
- `liquidation_event_rate`
- `liquidation_acceleration_usd`
- `liquidation_multiplier`
- `liquidation_directional_share`
- contiguous-bucket requirement for pairwise cascade metrics
- explicit immutable input lineage
- `method_version="uwbs-075-v1"`

No opaque composite cascade/risk score is introduced in UWBS-075.

## Acceptance evidence

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_derivatives/test_liquidation_cascade.py
12 passed in 1.83s

uv run pytest -q analysis/tests/crypto_derivatives
32 passed in 1.10s

uv run pytest -q analysis/tests
706 passed, 1 warning in 49.96s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not an UWBS-075 acceptance blocker.

## Handoff

Next v0.1.6 work item:

- **UWBS-076 — Position Map / OI retention**
- CP-076A: deterministic retained open-interest position map
- CP-076B: retention/change metrics with explicit provenance
