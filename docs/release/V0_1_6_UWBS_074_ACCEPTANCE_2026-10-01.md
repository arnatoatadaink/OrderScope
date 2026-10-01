# v0.1.6 UWBS-074 Acceptance — 2026-10-01

## Status

**Accepted**

UWBS-074 closes the deterministic crypto-derivatives archive and catch-up lifecycle semantics. Physical persistence, live catch-up network execution, retry/backoff, rate-limit orchestration, scheduler recovery, queueing, retention, compression, partitioning, historical backfill, and operational monitoring remain outside UWBS-074.

## Accepted scope

- deterministic snapshot envelope generation
- stable payload hashing
- venue/instrument/observed-time snapshot identity
- idempotent identical replay handling
- newer revision replacement
- stale revision rejection
- missing-window detection
- contiguous gap coalescing into catch-up windows
- catch-up lifecycle state transitions
- payload/input validation

## Acceptance evidence

Source head before this acceptance record:

- `709db5b94e2d7adcea8ce5566da8e3028dd420ee`

Executed locally on 2026-10-01:

```text
uv run pytest -q analysis/tests/crypto_archive/test_crypto_archive.py
10 passed in 1.22s

uv run pytest -q analysis/tests
694 passed, 1 warning in 50.50s

uv run python -m compileall -q analysis/app
PASS (no error output)

git diff --check
PASS (no output)
```

The single warning is an upstream Starlette TestClient / AnyIO `BlockingPortal` deprecation warning and is not an UWBS-074 acceptance blocker.

## Handoff

Next v0.1.6 work item:

- **UWBS-075 — Liquidation normalization / cascade metrics**
- CP-075A: source-neutral liquidation normalization
- CP-075B: deterministic cascade metrics with explicit lineage
