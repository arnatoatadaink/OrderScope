# OrderScope — L1-002 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `L1-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L1-001`

## 1. Local acceptance

User-reported local verification after the migration-regression hardening:

```text
storage migration tests -> 7 passed
focused L1-002 tests    -> 8 passed
full pytest suite       -> 368 passed
compileall              -> success
git diff --check        -> clean / no findings
```

The first full-suite run exposed two stale L0-005 assertions that assumed exactly one migration. Those assertions were corrected to derive expected version/count from the currently applied migration sequence; the second full run passed.

## 2. WBS completion boundary

L1-002 registers a small SQL fixture as immutable raw data and makes reimport of the same manifest/hash idempotent. It remains independent of the separately gated real D1 export (`L1-003`).

## 3. Implementation

- `analysis/app/orderscope_local/storage/sql/0002_raw_imports.sql`
- `analysis/app/orderscope_local/market_import/fixture_importer.py`
- `analysis/app/orderscope_local/market_import/__init__.py`
- `analysis/tests/market_import/test_fixture_dump_importer.py`
- `analysis/tests/storage/test_migrations.py` regression hardening

## 4. Accepted semantics

`import_fixture_dump()` verifies exact byte size and SHA-256 before storage. Raw artifacts are written beneath a caller-provided raw root using `d1/<sha256>.sql`; production/local callers keep that root beneath Git-ignored `var/`.

The `raw_imports` catalog stores manifest metadata, content hash, raw relative path, and registration time only. It never stores raw SQL rows.

Exact same manifest/hash reimport is `duplicate`, preserves the original registration time, and creates no second catalog row. Reuse of one artifact hash with different manifest meaning is rejected as conflict. Existing hash-addressed files must match supplied bytes exactly.

## 5. Migration integration

The L0-005 migration runner now applies `0001_catalog.sql` and `0002_raw_imports.sql`. Migration regression tests no longer hard-code a one-migration world; they verify `PRAGMA user_version` and migration count against the discovered/applied sequence so future migrations do not create false failures.

## 6. Explicit non-scope

L1-002 does not execute a real D1 export, parse arbitrary SQL into canonical bars, generate Parquet, run market-data quality checks, expose APIs, or start scheduling.

## 7. Lane state

```text
L0-005 Accepted
L1-001 Accepted
L1-002 Accepted
L1-003 Blocked on separate SMOKE-007 change window
L1-004 fixture path Ready
L1-005 waits for L1-004
```

## 8. Next action

Proceed to `L1-004 — Generate canonical bar dataset` on the fixture path. Preserve deterministic ordering and bar/receipt provenance; do not claim real-data completion until L1-003 is executed.
