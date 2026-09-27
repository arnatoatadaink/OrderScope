# UWBS-091 — M&A Integration / Legacy-System Evidence Overlay

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

## Purpose

Add a provider-neutral Physical-SaaS overlay for source-observed acquisition and integration milestones while keeping integration-quality judgments out of the Fact layer.

## Fact boundary

`IntegrationEventObservation` may record:

- acquisition announced / closed;
- platform migration started / completed;
- customer migration started / completed;
- legacy-system retirement;
- integration-program completion.

These are source assertions only. They do not establish that integration succeeded, that legacy drag exists, or that migration slippage occurred.

## Interpretation boundary

Supported assessment types:

- `integration_success_candidate`;
- `legacy_drag_candidate`;
- `migration_slippage_candidate`.

`SUPPORT` / `PARTIAL` require at least two independent evidence classes and always require integration-milestone evidence. Migration slippage additionally requires deployment-metric evidence. `CONTRADICT` requires explicit contradicting evidence. `UNKNOWN` carries no directional evidence.

Evidence references cannot be reused across integration-milestone, deployment-metric, financial-metric and contradicting classes.

## Layering rule

```text
source event -> Fact
reconciled deployment/funnel/financial measurements -> DerivedMetric
integration success / drag / slippage -> Interpretation
```

Acquisition close must never be silently promoted to integration success. Deployment observations must not be transformed into financial results, and financial improvement alone must not prove operational migration completion.

## Dependency

UWBS-091 depends on the accepted UWBS-088 milestone/reconciliation boundary and may consume downstream UWBS-089/UWBS-090 metrics as independent evidence classes.

## Runtime boundary

No live provider activation, Worker/Cron change, D1 mutation, PB authorization/execution, paid procurement or trading action is authorized by this task.
