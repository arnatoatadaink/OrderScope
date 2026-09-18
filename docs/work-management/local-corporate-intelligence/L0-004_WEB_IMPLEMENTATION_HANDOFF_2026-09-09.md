# OrderScope — L0-004 Web Implementation Handoff

Status: **Accepted — local verification complete**
Date: 2026-09-09
Task: `L0-004`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-002`

## 1. Acceptance evidence

User-reported local verification:

```text
focused L0-004 tests -> 11 passed
full pytest suite    -> 418 passed
git diff --check     -> clean / no findings
```

Two dependency deprecation warnings from FastAPI/Starlette/AnyIO were observed during focused tests. They are upstream-library warnings rather than functional failures and are not acceptance blockers for L0-004.

## 2. WBS completion boundary

L0-004 implements the minimal localhost health surface required by the local stack:

- `GET /health` returns bounded operational metadata;
- HTTP bind configuration is accepted only for literal `127.0.0.1`;
- external-interface, wildcard, hostname alias, and IPv6 binds are rejected fail-closed.

## 3. Changed/added files

- `analysis/app/orderscope_local/local_api/health.py`
- `analysis/app/orderscope_local/local_api/__init__.py`
- `analysis/tests/local_api/test_localhost_health.py`

## 4. Bind policy

`LocalServerBinding` accepts exactly:

```text
127.0.0.1
```

The contract deliberately does not resolve or normalize aliases. Therefore `0.0.0.0`, `localhost`, `::1`, wildcard/LAN/external addresses are rejected in v0.1.

## 5. Health contract

`GET /health` returns only:

```text
status = ok
schema_version = local-health-v0.1
bind_host = 127.0.0.1
```

The validated binding is retained on `app.state.local_binding` for reuse by later API/server entry points.

## 6. Security / mutation boundary

The health app exposes no credentials, provider/raw bodies, Facts, or mutation endpoints. Unknown routes return 404 and POST `/health` is not accepted.

## 7. Downstream gate

L0-004 is now Accepted. Together with Accepted X0-001 and X0-002, this opens `X0-003 — extend read-only API`.

L0-003 remains separately required before L0-006/X0-004 scheduler work.
