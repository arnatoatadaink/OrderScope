# OrderScope — L1-002 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `L1-002`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L1-001`

## 1. Local acceptance carried into this cycle

`L1-001` was promoted to Accepted from user-reported local evidence:

```text
focused L1-001 tests -> 8 passed
full pytest suite    -> 360 passed
git diff --check     -> clean / no findings
```

## 2. WBS completion boundary

L1-002 registers a small SQL fixture as immutable raw data and makes reimport of the same manifest/hash idempotent. It must not depend on the separately gated real D1 export (`L1-003`).

## 3. Changed/added files

- `analysis/app/orderscope_local/storage/sql/0002_raw_imports.sql`
- `analysis/app/orderscope_local/market_import/fixture_importer.py`
- `analysis/app/orderscope_local/market_import/__init__.py`
- `analysis/tests/market_import/test_fixture_dump_importer.py`

## 4. Storage model

The L0-005 migration foundation now applies `0002_raw_imports.sql`, which creates a strict `raw_imports` catalog table.

Catalog metadata includes:

- manifest ID / schema version;
- source environment and revision;
- half-open UTC window;
- table name;
- row count / byte size;
- artifact SHA-256;
- raw relative path;
- registration time.

The catalog does not store raw SQL rows.

## 5. Immutable raw artifact boundary

`import_fixture_dump()` receives the Accepted L1-001 `D1ExportManifest` plus artifact bytes. Before any registration it verifies:

```text
len(artifact) == manifest.byte_size
sha256(artifact) == manifest.sha256
```

The artifact is written beneath the caller-provided raw root using a content-addressed relative name:

```text
d1/<sha256>.sql
```

The repository-wide `.gitignore` already excludes `var/`; production/local callers should place the raw root there. Tests use temporary directories only.

## 6. Idempotency / conflict semantics

Exact same manifest/hash reimport:

```text
status = duplicate
same catalog row
same original registered_at
no second catalog row
```

A hash already registered under different manifest metadata is rejected as a conflict rather than silently reinterpreted.

If the hash-addressed path already exists, its bytes must exactly match the supplied artifact. Tampered or mismatched content is rejected.

## 7. Migration integration

`import_fixture_dump()` invokes the accepted versioned migration runner before catalog access. The focused fixtures verify that a new catalog reaches:

```text
PRAGMA user_version = 2
schema_migrations count = 2
```

This keeps physical catalog evolution behind the L0-005 migration contract rather than creating tables ad hoc in importer code.

## 8. Result boundary

`RawImportResult` contains only:

- `new` / `duplicate` status;
- manifest ID;
- SHA-256;
- raw relative path;
- UTC registration time.

It does not expose artifact bytes or parsed rows.

## 9. Focused fixtures encoded

The focused module contains 8 tests covering:

1. hash-addressed raw file and catalog registration;
2. same manifest/hash idempotent reimport;
3. byte-size/hash mismatch rejection before storage;
4. same hash with different manifest metadata conflict;
5. existing hash path with different bytes rejection;
6. migration version two/catalog-history integration;
7. UTC registration-time requirement;
8. result contains metadata and no raw body/rows.

## 10. Explicit non-scope

L1-002 does not:

- execute or approve a real D1 export;
- parse arbitrary SQL into canonical bars;
- generate Parquet;
- perform OHLCV/session/gap quality checks;
- expose import APIs;
- start the scheduler.

`L1-003` remains the independent real D1/SMOKE-007 change-window task. `L1-004` owns canonical bar dataset generation and may proceed on the fixture path after L1-002 acceptance.

## 11. Local verification boundary

Before promoting L1-002 to Accepted, run:

```bash
uv run pytest -q analysis/tests/market_import/test_fixture_dump_importer.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

## 12. Lane state

```text
L0-005 Accepted
L1-001 Accepted
L1-002 Provisional result — local test pending
L1-003 Blocked on separate SMOKE-007 change window
L1-004 waits for L1-002 acceptance (fixture path)
L1-005 waits for L1-004
```

## 13. Next action after acceptance

Proceed to `L1-004 — Generate canonical bar dataset` on the fixture path. Preserve deterministic ordering and bar/receipt provenance; do not claim real-data completion until the separate L1-003 change window is executed.
