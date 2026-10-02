# UWBS-089 — Deployment Funnel Derived Metrics / Slippage Interpretation

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**
Branch: `feat/uwbs-089-deployment-funnel`

## Purpose

Build deterministic deployment-funnel metrics on top of accepted UWBS-087 deployment Facts and UWBS-088 reconciliation without turning commercial guidance, cumulative installed base, backlog, billing, ARR, or revenue into deployment evidence.

## Accepted input boundary for calculation

Only observations satisfying all of the following may enter a stage aggregate:

- deployment state = `completed`;
- quantity basis = `event_increment`;
- explicit quantity exists;
- explicit quantity unit exists;
- compared stage quantities use the same unit;
- lineage record IDs are unique.

`planned`, `in_progress`, `cancelled`, `cumulative_base`, and `point_in_time_base` are excluded from the deterministic funnel calculation.

## DerivedMetric layer

For a comparable upstream/downstream stage pair:

```text
slippage_quantity = upstream_quantity - downstream_quantity
conversion_ratio  = downstream_quantity / upstream_quantity
```

`conversion_ratio` is omitted when upstream quantity is zero.

These outputs are `DerivedMetric` records with explicit input-record lineage. They are not Facts.

## Interpretation layer

The deterministic slippage rule emits one of:

```text
no_observed_slippage
observed_slippage
inconsistent_funnel
```

Rules:

```text
downstream == upstream -> no_observed_slippage
downstream <  upstream -> observed_slippage
downstream >  upstream -> inconsistent_funnel
```

`inconsistent_funnel` deliberately prevents a downstream-greater-than-upstream comparison from becoming a negative-slippage or growth conclusion. It indicates that the compared evidence/window/cohort needs review.

## Explicit non-goals

UWBS-089 does not infer:

- deployment delay cause;
- customer churn;
- contract conversion;
- billing commencement;
- ARR or revenue conversion;
- recurring-revenue quality;
- cash conversion;
- M&A integration quality.

Those belong to UWBS-090/UWBS-091 and later interpretation layers.

## Verification target

```text
analysis/tests/physical_saas/test_deployment_funnel.py
full analysis regression
python compileall
git diff --check
```

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action is authorized by this task.
