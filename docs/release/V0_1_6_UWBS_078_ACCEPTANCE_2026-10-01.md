# v0.1.6 UWBS-078 Acceptance — 2026-10-01

## Status

**Accepted**

UWBS-078 closes the NEAR futures-position Canary composition layer.

## Accepted scope

- NEAR-only futures/perpetual monitoring snapshot
- cross-venue median OI / funding / mark context
- cross-venue OI / funding / mark mismatch diagnostics
- weighted Position Map OI-retention context
- long / short liquidation aggregation
- liquidation directional share
- deterministic QA flags
- stable deduplicated lineage
- `method_version="uwbs-078-v1"`

The Canary remains descriptive/experimental. It does not emit price-direction forecasts, buy/sell recommendations, trader identity, an exact position ledger, or an opaque composite score.

## Acceptance evidence

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_derivatives/test_near_futures_canary.py
10 passed in 1.15s

uv run pytest -q analysis/tests/crypto_derivatives
62 passed in 1.72s

uv run pytest -q analysis/tests
736 passed, 1 warning in 34.82s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not an UWBS-078 acceptance blocker.

## Handoff

Next canonical v0.1.6 work item:

- **UWBS-079 — Pacific weekend handoff / weekday re-risking validation**
- CP-079A: experimental weekend handoff / weekday re-risking validation
- Requires UWBS-071 plus UWBS-073..078 outputs.
