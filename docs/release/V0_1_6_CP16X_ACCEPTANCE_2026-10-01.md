# OrderScope v0.1.6 CP-16X Acceptance — 2026-10-01

## Status

**Development Release Accepted**

CP-16X closes the v0.1.6 crypto lane implementation boundary after focused package validation, full Python regression, compile validation, and diff hygiene checks.

## Acceptance evidence

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_derivatives
62 passed in 2.66s

uv run pytest -q analysis/tests/crypto_canary
20 passed in 1.84s

uv run pytest -q analysis/tests/crypto_context
9 passed in 1.82s

uv run pytest -q analysis/tests/crypto_time
10 passed in 1.04s

uv run pytest -q analysis/tests/crypto_archive
10 passed in 1.00s

uv run pytest -q analysis/tests
746 passed, 1 warning in 33.78s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is the pre-existing Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not a v0.1.6 acceptance blocker.

## Accepted v0.1.6 crypto-lane scope

Canonical tasks UWBS-068 through UWBS-079 are implemented within the v0.1.6 development-release boundary, including:

- crypto derivatives contracts and derived metrics
- BTC-relative crypto context
- institutional-flow/source survey governance
- 24/7 crypto time-window semantics
- NEAR/BTC Canary
- multi-venue futures/perpetual adapters
- durable derivatives archive and catch-up lifecycle
- liquidation normalization and cascade metrics
- Position Map / OI retention estimation
- cross-venue divergence and data-quality guards
- NEAR futures-position Canary
- Pacific weekend handoff / weekday re-risking validator

## Explicit remaining experimental boundary

UWBS-079 Stage A (code implementation and regression) is Accepted.

UWBS-079 Stage B remains **Experimental / empirical validation pending** because recurrence requires a multi-week set of independent real-data weekends. This does not block v0.1.6 Development Release acceptance, but it does block any claim that weekend-to-weekday re-risking recurrence has been empirically validated.

Do not upgrade the following without Stage B evidence:

- recurrence strength
- stable lag claims
- stable breadth claims
- causal BTC leadership claims
- participant-geography attribution
- universal weekend re-risking thresholds

## Release decision

```text
v0.1.6 crypto implementation boundary  = ACCEPTED
full Python regression                 = ACCEPTED
compile / diff hygiene                 = ACCEPTED
UWBS-079 Stage A                       = ACCEPTED
UWBS-079 Stage B recurrence evidence   = PENDING / EXPERIMENTAL
```
