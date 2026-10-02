# UWBS-092 — Physical-SaaS Applicability Guard

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

## Purpose

Prevent Physical-SaaS-specific deployment, financial-quality, M&A-integration, and Canary logic from being applied to subjects whose business model is not sufficiently evidenced as Physical-SaaS.

## Boundary

Applicability is an Interpretation, not a company Fact.

A clean `APPLICABLE` result requires both:

1. source-grounded physical-deployment evidence; and
2. source-grounded recurring-service or recurring-revenue evidence.

Additional evidence classes may include connected operations and customer-workflow embedding.

The following are insufficient by themselves:

- one hardware shipment;
- one software product;
- one subscription/ARR metric;
- one acquisition event;
- one connected-device count.

Unresolved contradictory evidence prevents the downstream guard from opening.

## Ratings

```text
applicable
conditional
not_applicable
unknown
```

Only `applicable` sets `downstream_allowed=true`.

## Fact / DerivedMetric / Interpretation separation

- source observations remain Facts;
- deterministic financial calculations remain DerivedMetrics;
- Physical-SaaS applicability remains Interpretation;
- no applicability result creates ARR, revenue, deployment, integration-success, or valuation Facts.

## Runtime boundary

No live provider activation, Worker/Cron/D1 mutation, PB execution, paid procurement, or trading action is authorized by this task.
