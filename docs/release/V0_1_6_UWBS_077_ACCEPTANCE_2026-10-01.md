# v0.1.6 UWBS-077 Acceptance — 2026-10-01

## Status

**Accepted**

UWBS-077 closes the cross-venue derivatives quality-assurance layer. It compares aligned observations across venues without treating any venue or the median as ground truth.

## Accepted scope

- same instrument / contract-type comparison
- duplicate venue rejection
- bounded observation-time skew
- deterministic venue ordering
- open-interest USD comparison
- funding-rate comparison
- mark-price comparison
- median center as descriptive statistic only
- maximum absolute deviation
- maximum relative deviation
- immutable observation lineage
- `method_version="uwbs-077-v1"`

## Acceptance evidence

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_derivatives/test_cross_venue_qa.py
10 passed in 0.98s

uv run pytest -q analysis/tests/crypto_derivatives
52 passed in 1.93s

uv run pytest -q analysis/tests
726 passed, 1 warning in 44.37s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not an UWBS-077 acceptance blocker.

## Handoff

Next v0.1.6 crypto-lane work item:

- **UWBS-078 — NEAR futures-position Canary**
- Consume accepted derivatives normalization, archive, liquidation, Position Map, and cross-venue QA outputs.
- Keep inference boundaries explicit: no trader identity, no exact position ledger, and no opaque composite score.
