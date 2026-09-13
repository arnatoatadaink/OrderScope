# Pytest SQLite ResourceWarning Investigation Report

- Date: 2026-09-14 (JST)
- Scope: `PYTHONPATH=analysis/app uv run pytest -q`
- Status: root cause identified; no application or test fix applied

## Executive summary

The pytest failures are not assertion or business-logic failures. Python 3.13 reports
garbage-collected, unclosed `sqlite3.Connection` objects as `ResourceWarning`, and the
repository-wide pytest policy promotes every warning to an error. The apparent failing
test names depend on garbage-collection timing and therefore do not reliably identify
the code that allocated the leaked connection.

With a writable temporary uv cache, the full suite produced:

```text
3 failed, 592 passed in 21.00s
```

All three failures were pytest unraisable-exception groups containing one or more:

```text
ResourceWarning: unclosed database in <sqlite3.Connection ...>
pytest.PytestUnraisableExceptionWarning: Exception ignored in: <sqlite3.Connection ...>
```

## Reproduction notes

The exact requested command could not initially enter pytest in the managed investigation
environment because uv's default cache directory was read-only:

```text
error: Could not acquire lock
Caused by: Could not create temporary file
Caused by: Read-only file system ... at path "/home/y/.cache/uv/..."
```

The tests were therefore run with only the cache location changed:

```bash
UV_CACHE_DIR=/tmp/orderscope-pytest-investigation \
PYTHONPATH=analysis/app uv run pytest -q
```

The reported failing test nodes were:

1. `analysis/tests/news/test_news_contradiction_review.py::test_every_review_reason_kind_is_versioned_and_accepted[ambiguous_value]`
2. `analysis/tests/sec/test_filing_records.py::test_same_accession_with_changed_hash_is_an_explicit_conflict`
3. `analysis/tests/storage/test_migrations.py::test_empty_databases_rebuild_to_identical_catalog_schema`

These are collection points for the warnings, not necessarily the allocation sites.

## Root cause

`pyproject.toml` configures pytest as follows:

```toml
[tool.pytest.ini_options]
filterwarnings = [
  "error",
  # one narrow Starlette/AnyIO exception follows
]
```

Consequently, the SQLite resource warnings are suite failures. The strict warning policy
exposed connection-lifecycle defects that were previously silent.

Python's SQLite connection context manager controls transaction commit/rollback behavior;
leaving this context does not close the connection. Code such as the following therefore
leaks the connection until garbage collection:

```python
with sqlite3.connect(database) as connection:
    ...
```

An explicit `close()`, a `try/finally`, or `contextlib.closing()` is required when the
current function owns the connection.

## Confirmed allocation evidence

The SEC filing-record test module was rerun with allocation tracing:

```bash
UV_CACHE_DIR=/tmp/orderscope-pytest-investigation \
PYTHONTRACEMALLOC=10 \
PYTHONPATH=analysis/app \
uv run pytest -q analysis/tests/sec/test_filing_records.py
```

Its assertions all passed (`10 passed`), but pytest still exited with code 1 during
session cleanup. Tracemalloc identified 11 unclosed connections, including allocations
from:

- `analysis/tests/sec/test_filing_records.py:15`, where `repository()` creates an
  in-memory connection and returns a repository without arranging teardown;
- `analysis/tests/sec/test_filing_records.py:139`, where a test directly creates an
  in-memory connection without closing it.

This demonstrates that the pytest failure is a resource-lifecycle problem independent
of the filing-record assertions.

## Wider affected surface

A repository search found additional connection ownership that must be audited as one
repair set. Notable sites include:

- `analysis/tests/storage/test_migrations.py`: four uses of
  `with sqlite3.connect(...)` that do not close the connection;
- `analysis/tests/market_import/test_fixture_dump_importer.py`: three equivalent
  context-manager uses;
- `analysis/tests/sec/test_filing_detection_acceptance.py`;
- `analysis/tests/sec/test_form_filter.py`;
- `analysis/tests/storage/test_d1_bounded_export.py`;
- `analysis/tests/storage/test_d1_drain_failure_fixture.py`;
- `analysis/app/orderscope_local/market_import/fixture_importer.py`: production code
  using the same non-closing context-manager pattern.

Some other call sites already use `try/finally` and close correctly, including the
migration runner, restore drill, and canonical-bar fixture reader. Every call site should
still be classified by connection ownership before editing.

## Recommended repair

1. Preserve the strict warning policy; it is correctly detecting real resource leaks.
2. For short-lived owned connections, use explicit deterministic closure, for example:

   ```python
   from contextlib import closing

   with closing(sqlite3.connect(database)) as connection:
       ...
   ```

3. Where transaction semantics are required in addition to closure, nest the SQLite
   transaction context within `closing(...)`, or use `try/finally` with explicit
   commit/rollback behavior.
4. Convert reusable pytest repository/connection helpers into `yield` fixtures whose
   teardown calls `connection.close()`.
5. Close directly created connections in negative-path tests as well as success paths.
6. Run the full suite with warnings treated as errors and, if necessary, repeat once with
   `PYTHONTRACEMALLOC=10` to prove that no delayed SQLite warnings remain.

Fixing only the three displayed failing tests is insufficient: garbage-collection timing
can move the same warnings to different tests or to pytest session cleanup.

## Repository state during investigation

- Branch: `docs/mermaid-conventions-v0.1`
- Before this report, local `HEAD` and its upstream were synchronized (`0 ahead, 0 behind`).
- `uv.lock` was already present as an unrelated unstaged modification and was intentionally
  excluded from this report change.
