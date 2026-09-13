# OrderScope — L0-003 Web Implementation Handoff

Status: **Accepted**
Date: 2026-09-09
Task: `L0-003`
Parent WBS: `WORK_BREAKDOWN_LOCAL_CORPORATE_INTELLIGENCE_2026-09-03.md`
Depends on: Accepted `L0-002`

## 1. Completion boundary

L0-003 implements the local non-secret configuration and secret-handling boundary required before `L0-006`.

Implemented files:

- `analysis/app/orderscope_local/config.py`
- `analysis/tests/config/test_config.py`
- `analysis/config/README.md`

No provider request, remote D1 operation, Worker change, HTTP mutation route, or secret value was added.

## 2. Non-secret configuration schema

`LocalConfig` contains only:

```text
data_root: pathlib.Path
log_level: CRITICAL | ERROR | WARNING | INFO | DEBUG
sec_user_agent: optional non-secret string
```

Environment names:

```text
ORDERSCOPE_DATA_ROOT
ORDERSCOPE_LOG_LEVEL
ORDERSCOPE_SEC_USER_AGENT
```

Default data root remains logical `var/`; operational WSL runs may override it with a WSL-native path without committing machine-specific configuration.

## 3. Secret boundary

Registered credential environment names:

```text
ORDERSCOPE_SECRET_ALPACA_API_KEY
ORDERSCOPE_SECRET_ALPACA_API_SECRET
```

Rules:

- all OrderScope credentials use the `ORDERSCOPE_SECRET_` prefix;
- secret values are absent from `LocalConfig`;
- a secret must be explicitly registered before `read_required_secret()` accepts it;
- missing credentials fail closed and error messages identify the variable name, never the value;
- `redact_environment_for_logging()` redacts every `ORDERSCOPE_SECRET_*` value, including future-prefixed variables;
- unrelated environment variables are excluded from the logging projection.

## 4. Local-only credential procedure

The configuration README specifies:

1. credentials stay in the local WSL process/session environment or another Git-excluded local mechanism;
2. no secrets in committed config/dotenv, CLI arguments, tests, dumps, API responses, or manifests;
3. adapters read only their registered secret at point of use;
4. logging uses secret-free config fields or the redaction helper;
5. tests use synthetic mappings and do not read the operator environment.

## 5. Focused tests

The focused module contains 9 cases covering:

1. safe defaults;
2. non-secret environment loading while secret values remain outside config state;
3. invalid log-level rejection;
4. blank SEC user-agent rejection;
5. registered secret retrieval without entering config;
6. missing-secret failure without value exposure;
7. unregistered secret-name rejection;
8. prefix-wide logging redaction including a future provider token;
9. secret-free `LocalConfig.log_fields()` projection.

## 6. Local acceptance evidence

Observed user-reported evidence on 2026-09-09:

```text
focused config tests -> 9 passed
full pytest suite    -> 441 passed
compileall           -> success / no errors
git diff --check     -> clean / no findings
```

All required checks passed. L0-003 is Accepted.

## 7. Next action after acceptance

```text
L0-003 Accepted
  -> L0-006 CLI entry point
  -> X0-004 local scheduler
```

`L1-006` remains an independently Ready read-only API extension. `L1-003` / `SMOKE-007` real-D1 work remains separately gated.
