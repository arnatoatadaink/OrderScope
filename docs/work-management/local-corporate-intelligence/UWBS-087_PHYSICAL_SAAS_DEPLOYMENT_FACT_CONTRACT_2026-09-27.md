# UWBS-087 — Physical-SaaS Deployment Lifecycle Fact Contract — 2026-09-27

Status: **IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Branch: `l1-003-local-market-recovery`

## Purpose

Define a provider-neutral Fact boundary for source-observed Physical-SaaS deployment lifecycle milestones without converting commercial pipeline, management guidance or recurring-revenue outcomes into deployment Facts.

Canonical dependency source: `WBS_PROVISIONAL_ID_REGISTRY.md`.

```text
UWBS-087 -> UWBS-088 -> UWBS-089
UWBS-087 -> UWBS-090
UWBS-087 -> UWBS-092
```

## Contract

Implementation:

`analysis/app/orderscope_local/contracts/physical_saas_deployment.py`

Normalized lifecycle milestones:

```text
shipped
delivered
installed
activated
operational
customer_accepted
decommissioned
```

Source completion state is retained independently:

```text
planned
in_progress
completed
cancelled
```

Optional quantities preserve their source meaning through an explicit quantity basis:

```text
event_increment
cumulative_base
point_in_time_base
```

A quantity is never accepted without both a source unit and quantity basis.

## Semantic guards

The Fact layer must preserve these distinctions:

- shipped != delivered;
- delivered != installed;
- installed != activated;
- activated != operational;
- operational != customer acceptance;
- planned != completed;
- cumulative connected/installed base != period deployment increment;
- backlog/bookings/contract value != deployment;
- deployment != billing;
- deployment != ARR;
- deployment != recognized revenue;
- management target/guidance != realized deployment.

Commercial conversion, recurring-revenue quality and cash conversion belong downstream, especially UWBS-089/UWBS-090.

## Materialization

`PhysicalSaasDeploymentObservation.to_fact()` materializes:

```text
schema_version = physical-saas-deployment-observation-v0.1
fact_type      = physical_saas_deployment.<milestone>
assertion_kind = observation
```

The effective source interval is carried through Fact `period_start` / `period_end`.

## Local verification

```bash
uv run pytest -q \
  analysis/tests/contracts/test_physical_saas_deployment.py

uv run pytest -q analysis/tests

uv run python -m compileall -q analysis/app

git diff --check
```

Expected focused count before concurrent changes:

```text
Physical-SaaS deployment contract: 10 tests
```

## Boundary

This task performs no provider activation, Worker/Cron change, D1 mutation, paid procurement, PB execution or trading action.
