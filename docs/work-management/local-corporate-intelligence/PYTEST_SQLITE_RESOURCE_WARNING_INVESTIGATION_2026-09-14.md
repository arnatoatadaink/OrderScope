# Pytest SQLite ResourceWarning Investigation Report

- Date: 2026-09-14 (JST)
- Scope: `PYTHONPATH=analysis/app uv run pytest -q`
- Status: **Accepted locally — root cause fixed and full-suite verification clean**

## Executive summary

Python 3.13 exposed unclosed `sqlite3.Connection` objects as `ResourceWarning`, and the repository-wide strict pytest warning policy correctly promoted those warnings to failures. The failures were resource-lifecycle defects, not business-logic or assertion failures.

The repair set closed owned SQLite connections deterministically in production fixture-import code and in test fixtures/helpers. Short-lived owned connections now use explicit closure (`contextlib.closing()` or fixture teardown), and reusable pytest repository fixtures use `yield` teardown where appropriate.

Final acceptance evidence supplied from the local environment:

```text
PYTHONPATH=analysis/app uv run pytest -q
595 passed in 20.93s

PYTHONTRACEMALLOC=10 PYTHONPATH=analysis/app uv run pytest -q
595 passed in 43.12s
```

No `ResourceWarning`, `PytestUnraisableExceptionWarning`, or delayed SQLite connection warning remained in either run.

## Original failure

Before repair, strict warning handling produced:

```text
3 failed, 592 passed in 21.00s
```

The displayed test names were garbage-collection collection points rather than reliable allocation sites. Tracemalloc confirmed unclosed SQLite connections, including allocations in `analysis/tests/sec/test_filing_records.py`.

## Root cause

The SQLite connection context manager controls transaction commit/rollback behavior; leaving `with sqlite3.connect(...) as connection:` does not close the connection. Owned connections therefore require an explicit `close()`, `try/finally`, `contextlib.closing()`, or teardown fixture.

## Repair set

The accepted repair covered the investigated ownership surface, including:

- `analysis/app/orderscope_local/market_import/fixture_importer.py`;
- `analysis/tests/storage/test_migrations.py`;
- `analysis/tests/market_import/test_fixture_dump_importer.py`;
- `analysis/tests/sec/test_filing_detection_acceptance.py`;
- `analysis/tests/sec/test_form_filter.py`;
- `analysis/tests/sec/test_filing_records.py`;
- `analysis/tests/storage/test_d1_bounded_export.py`;
- `analysis/tests/storage/test_d1_drain_failure_fixture.py`.

Production and test ownership are now explicit: callers that create the connection close it; repositories that receive a connection do not invent ownership.

## Warning-policy disposition

The strict warning policy remains in force. The separately documented Starlette 1.6.0 / AnyIO `BlockingPortal` compatibility warning remains the only narrow upstream exception. SQLite warnings are not suppressed.

## Acceptance boundary

This maintenance acceptance changes no Worker, Cron, D1 remote state, provider credentials, market-data semantics, or release gate. It is a local dependency/resource-lifecycle repair only.

## Repository state note

`uv.lock` was intentionally kept separate from the original investigation report because it was an unrelated local modification at that time. This acceptance does not reinterpret unrelated lockfile changes.
