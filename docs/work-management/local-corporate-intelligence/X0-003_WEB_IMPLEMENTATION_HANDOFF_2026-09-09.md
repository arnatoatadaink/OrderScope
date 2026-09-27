# OrderScope — X0-003 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `X0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-004`, Accepted `X0-001`, Accepted `X0-002`

## 1. Local acceptance carried into this cycle

`L0-004` is Accepted from user-reported local evidence:

```text
focused L0-004 tests -> 11 passed
full pytest suite    -> 418 passed
git diff --check     -> clean / no findings
```

The focused run also emitted two upstream dependency deprecation warnings from FastAPI/Starlette/AnyIO. They were non-failing warnings and are not treated as an L0-004 acceptance blocker.

## 2. WBS completion boundary

X0-003 extends the accepted localhost-only FastAPI surface with read-only endpoints:

```text
GET /facts
GET /filings
GET /earnings
GET /news
GET /sources/health
```

`GET /health` remains available under the same literal `127.0.0.1` bind contract.

No HTTP mutation route is introduced.

## 3. Changed/added files

- `analysis/app/orderscope_local/local_api/read_api.py`
- `analysis/app/orderscope_local/local_api/__init__.py`
- `analysis/tests/local_api/test_read_api.py`

## 4. Read snapshot boundary

`LocalReadSnapshot` receives immutable tuples of accepted `Fact` and optional market timeline records plus an optional accepted `CorporateCoverageSummary`.

The HTTP layer does not acquire data, persist data, resolve provider cursors, delete content, or mutate Fact Store state.

## 5. Facts API

`GET /facts` is an as-of-safe read over accepted Facts.

A Fact is visible only when:

```text
provenance.available_at <= as_of
accepted_at <= as_of
```

Optional `subject_ref` filtering is exact. The API does not infer ticker aliases or entity relationships.

Response fields are bounded durable Fact metadata/value fields including record ID, schema, subject, fact type, assertion kind, storage-neutral value, unit, available/accepted times, source ref/hash, and evidence record IDs.

Raw provider bodies, raw news bodies, credentials, and temporary content are not returned.

## 6. Domain endpoints

`/filings`, `/earnings`, and `/news` reuse the accepted X0-001 conservative source-kind classification and as-of behavior. They do not create a second classification policy in the HTTP layer.

The routes expose the underlying Fact records selected by the timeline classification, preserving deterministic ordering by availability, acceptance, and record ID.

## 7. Source-health endpoint

`GET /sources/health` serializes the accepted X0-002 `CorporateCoverageSummary` without recomputing provider health state.

It exposes only sanitized coverage fields such as last success, latest checkpoint state, opaque cursor, lag, sanitized error/retry state, and retention pending/overdue metadata.

If no coverage snapshot is supplied, the endpoint returns an explicit empty source list rather than fabricating health.

## 8. Localhost / mutation boundary

`create_read_app()` reuses `LocalServerBinding`; therefore only literal `127.0.0.1` is accepted.

No POST/PUT/PATCH/DELETE route is defined for the X0-003 resources. Mutation remains outside HTTP and is reserved for later CLI-controlled workflows.

## 9. Versioned API contract

Schema version:

```text
local-read-api-v0.1
```

Collection responses include the schema version, collection name, as-of instant, count, and deterministic items.

## 10. Focused fixtures encoded

The focused module collects 14 cases covering:

1. health/bind contract reuse;
2. as-of-safe `/facts` ordering/value serialization;
3-5. filing/earnings/news domain isolation;
6. exact subject filtering with no alias guessing;
7. coverage serialization;
8. absent coverage without fabrication;
9. HTTP mutation rejection;
10-13. wildcard/alias/IPv6/LAN bind rejection;
14. immutable Fact snapshot boundary.

## 11. Explicit non-scope

X0-003 does not:

- implement `/imports`, `/datasets`, or `/quality/latest` (L1-006 scope);
- start Uvicorn or implement CLI `serve` (L0-006 scope);
- start or control scheduler jobs;
- expose raw source bodies or credentials;
- execute real D1 export;
- authenticate remote clients because remote binds are prohibited in v0.1.

## 12. Local verification evidence

Executed locally:

```text
uv run pytest -q analysis/tests/local_api/test_read_api.py -> 14 passed
uv run pytest -q                                      -> 432 passed
python3 -m compileall -q analysis/app analysis/tests  -> success / no errors
git diff --check                                      -> clean / no findings
```

All X0-003 acceptance gates passed. `X0-003 = Accepted`.

## 13. Next action after acceptance

The remaining path to X0-004 scheduler runs through Local foundation:

```text
L0-003 config/secret boundary
  -> L0-006 CLI entry point
  -> X0-004 local scheduler
```

L1-003 real D1 export remains a separate approved change-window gate and must not be conflated with fixture-path API acceptance.
