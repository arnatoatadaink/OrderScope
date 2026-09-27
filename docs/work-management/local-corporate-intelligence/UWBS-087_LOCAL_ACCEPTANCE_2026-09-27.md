# UWBS-087 — Local Acceptance

Status: **ACCEPTED**
Date: 2026-09-27
Task: Define Physical-SaaS deployment lifecycle Fact contract

## Accepted implementation

- `analysis/app/orderscope_local/contracts/physical_saas_deployment.py`
- `analysis/tests/contracts/test_physical_saas_deployment.py`
- `docs/work-management/local-corporate-intelligence/UWBS-087_PHYSICAL_SAAS_DEPLOYMENT_FACT_CONTRACT_2026-09-27.md`

## Local verification

```text
physical-SaaS deployment focused tests: 10 passed in 1.95s
full Python regression:                845 passed in 47.84s
compileall:                            PASS
git diff --check:                     PASS
```

## Accepted boundary

The Fact layer records source-observed physical lifecycle milestones and preserves milestone state plus quantity basis. It does not convert backlog, bookings, contract value, connected/cumulative base, billing, ARR, recognized revenue, or management targets into completed deployment Facts.

Milestones:

```text
shipped
delivered
installed
activated
operational
customer_accepted
decommissioned
```

Lifecycle assertion states:

```text
planned
in_progress
completed
cancelled
```

Quantity bases:

```text
event_increment
cumulative_base
point_in_time_base
```

A cumulative or point-in-time installed/connected base must not be silently treated as a period deployment increment.

## Authorization boundary

This acceptance does not authorize live provider activation, paid procurement, Worker/Cron mutation, D1 mutation, PB execution, or trading action.
