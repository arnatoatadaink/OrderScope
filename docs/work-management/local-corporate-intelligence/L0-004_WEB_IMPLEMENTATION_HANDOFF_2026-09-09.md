# OrderScope — L0-004 Web Implementation Handoff

Status: **Provisional result — Web implementation complete / local test pending**
Date: 2026-09-09
Task: `L0-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-002`

## 1. Local acceptance carried into this cycle

`X0-002` is Accepted from user-reported local evidence:

```text
focused X0-002 tests -> 9 passed
full pytest suite    -> 407 passed
git diff --check     -> clean / no findings
```

This leaves L0-004 as the only explicit unsatisfied dependency for X0-003 because X0-001 and X0-002 are now Accepted.

## 2. WBS completion boundary

L0-004 implements the minimal localhost health surface required by the local stack:

- `GET /health` returns bounded operational metadata;
- HTTP bind configuration is accepted only for literal `127.0.0.1`;
- external-interface, wildcard, hostname alias, and IPv6 binds are rejected fail-closed.

It does not yet expose facts, filings, earnings, news, source coverage, import state, or mutation endpoints.

## 3. Changed/added files

- `analysis/app/orderscope_local/local_api/health.py`
- `analysis/app/orderscope_local/local_api/__init__.py`
- `analysis/tests/local_api/test_localhost_health.py`

## 4. Bind policy

`LocalServerBinding` accepts exactly:

```text
127.0.0.1
```

The contract deliberately does not resolve or normalize aliases. Therefore the following are rejected in v0.1:

```text
0.0.0.0
localhost
::1
::
LAN/private addresses
externally routable addresses
```

This is stricter than merely checking for a loopback-capable hostname and prevents a later server entrypoint from silently widening exposure.

## 5. Health contract

`create_health_app()` creates a FastAPI app after validating the bind contract.

`GET /health` returns only:

```text
status = ok
schema_version = local-health-v0.1
bind_host = 127.0.0.1
```

The validated binding is retained on `app.state.local_binding` so the later CLI/server entrypoint can use the same already-validated host rather than accepting an independent host string.

## 6. Security / mutation boundary

The L0-004 app does not expose provider credentials, paths, raw provider bodies, raw news bodies, Facts, or source data.

No mutation route is defined. Unknown routes return 404 and POST `/health` is not accepted.

## 7. Focused fixtures encoded

The focused module currently collects 11 cases (6 test functions including a 6-case parametrization) covering:

1. default exact IPv4 loopback bind;
2. rejection of wildcard/alias/IPv6/LAN bind values;
3. exact bounded `/health` response;
4. validated binding retained for the later server entrypoint;
5. no accidental `/facts` or mutation surface in the health-only app;
6. unvalidated binding object rejection.

## 8. Explicit non-scope

L0-004 does not:

- start Uvicorn;
- implement CLI `serve`;
- expose X0-003 read-only endpoints;
- implement authentication;
- expose externally accessible interfaces;
- start ingestion or scheduler jobs from HTTP.

`X0-003` extends this local read-only application only after L0-004 acceptance. `L0-006` later owns the CLI entry point and must reuse the localhost bind contract.

## 9. Local verification boundary

Run:

```bash
uv run pytest -q analysis/tests/local_api/test_localhost_health.py
uv run pytest -q
python3 -m compileall -q analysis/app analysis/tests
git diff --check
```

Acceptance requires focused tests, full regression, compileall success, and clean diff check.

## 10. Lane state

```text
X0-001 Accepted
X0-002 Accepted
L0-004 Provisional result — local verification pending
X0-003 waits only for L0-004 acceptance
L0-003 remains Ready and is still needed before L0-006/X0-004
```

## 11. Next action after acceptance

After L0-004 acceptance, proceed directly to `X0-003 — extend read-only API` with `/facts`, `/filings`, `/earnings`, `/news`, and `/sources/health`, keeping the literal 127.0.0.1 bind and HTTP mutation prohibition intact.
