# UWBS-089 — Local Acceptance

Status: **ACCEPTED**
Date: 2026-09-27
Branch: `feat/uwbs-089-deployment-funnel`

## Scope

UWBS-089 implements Physical-SaaS deployment-funnel Derived Metrics and bounded slippage interpretation on top of accepted UWBS-087 deployment Facts and UWBS-088 reconciliation.

The accepted boundary is intentionally non-commercial:

- only completed `EVENT_INCREMENT` deployment observations are eligible for funnel arithmetic;
- quantity units must match before quantities are compared;
- cumulative/point-in-time installed-base observations are not silently converted into period increments;
- planned/in-progress/cancelled observations do not contribute completed-stage quantities;
- downstream quantity greater than upstream quantity is classified as an inconsistent funnel rather than a negative-slippage success signal;
- deployment metrics are not converted into billing, ARR, recognized revenue, or causal explanations.

## Local verification

```text
UWBS-089 focused tests: 10 passed in 1.71s
full Python regression: 864 passed in 33.47s
compileall: PASS
git diff --check: PASS
```

Commands:

```bash
uv run pytest -q analysis/tests/physical_saas/test_deployment_funnel.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

## Acceptance result

**ACCEPTED**

UWBS-089 may be used as an accepted prerequisite for the remaining Physical-SaaS lane. This acceptance does not authorize live provider activation, Worker/Cron/D1 mutation, PB execution, paid procurement, or trading action.
