# v0.1.6 UWBS-076 Acceptance — 2026-10-01

## Status

**Accepted**

UWBS-076 closes the deterministic Position Map / OI-retention estimate layer.

## Accepted scope

- price-band anchoring of positive OI growth
- explicit distinction between aggregate inference and a true trader-level position ledger
- retained OI estimate capped at the original anchor OI addition
- retention ratio in [0, 1]
- anchor funding-rate context
- same-series post-anchor long/short liquidation context
- explicit immutable input lineage
- `method_version="uwbs-076-v1"`
- configurable price-band width

## Acceptance evidence

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_derivatives/test_position_map.py
10 passed in 1.74s

uv run pytest -q analysis/tests/crypto_derivatives
42 passed in 1.75s

uv run pytest -q analysis/tests
716 passed, 1 warning in 36.73s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not an UWBS-076 acceptance blocker.

## Handoff

Next v0.1.6 work item:

- **UWBS-077 — Cross-venue mismatch / derivatives QA**
- CP-077A: comparable cross-venue snapshot grouping
- CP-077B: deterministic mismatch diagnostics without provider-ranking assumptions
