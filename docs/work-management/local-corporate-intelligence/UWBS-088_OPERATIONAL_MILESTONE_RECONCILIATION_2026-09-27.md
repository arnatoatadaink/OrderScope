# UWBS-088 — Operational Milestone Extraction and Reconciliation

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**
Date: 2026-09-27
Dependency: UWBS-087 ACCEPTED

## Purpose

Normalize source-observed Physical-SaaS operational milestones through the UWBS-087 contract and reconcile overlapping assertions without silently selecting a winner.

## Reconciliation statuses

```text
consistent
 duplicate
conflict
insufficient_identity
```

## Identity rule

Preferred identity anchor:

```text
deployment_ref + milestone
```

Fallback identity anchor:

```text
customer_ref + site_ref + milestone
```

If neither anchor is available, the reconciliation result is `insufficient_identity`; potentially unrelated records must not be forced into a conflict.

## Conflict dimensions

For records that resolve to the same deployment milestone identity, the following differences are preserved as explicit conflicts:

```text
state
quantity
quantity_unit
quantity_basis
effective_start
effective_end
customer_ref
site_ref
product_ref
```

In particular, `cumulative_base` and `event_increment` are not interchangeable.

## Duplicate rule

Two assertions with the same normalized identity, content fields and provenance are classified as `duplicate`.

Two assertions with the same normalized content but independent provenance are classified as `consistent`, not duplicate.

## Non-goals

UWBS-088 does not:

- infer revenue, ARR, billing or cash collection;
- convert backlog/bookings/guidance into deployment milestones;
- compute deployment-funnel conversion or slippage metrics;
- choose a preferred source when assertions conflict;
- perform M&A/legacy-system interpretation.

Those belong to downstream UWBS-089..093 work.

## Implementation

- `analysis/app/orderscope_local/physical_saas/milestone_reconciliation.py`
- `analysis/tests/physical_saas/test_milestone_reconciliation.py`

## Acceptance gate

Required local checks:

```bash
uv run pytest -q analysis/tests/physical_saas/test_milestone_reconciliation.py
uv run pytest -q analysis/tests
uv run python -m compileall -q analysis/app
git diff --check
```

No live provider activation, paid procurement, Worker/Cron mutation, D1 mutation, PB execution, or trading action is authorized by this task.
