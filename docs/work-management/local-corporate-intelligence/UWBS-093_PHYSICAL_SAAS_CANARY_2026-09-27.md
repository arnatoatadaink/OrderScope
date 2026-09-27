# UWBS-093 — Physical-SaaS Canary

Status: **IMPLEMENTED / LOCAL ACCEPTANCE PENDING**

## Purpose

Close the Physical-SaaS lane with a held-out Canary that combines the accepted UWBS-089 deployment-funnel, UWBS-090 financial-quality, UWBS-091 integration-overlay and UWBS-092 applicability boundaries without collapsing Fact, DerivedMetric and Interpretation layers.

## Guard

The Canary is evaluated only after the UWBS-092 applicability result opens the downstream lane. A non-applicable, conditional or unknown subject cannot be treated as a clean Physical-SaaS support case.

## Signal classes

The Canary keeps three independent downstream classes:

- deployment-funnel evidence;
- financial-quality evidence;
- M&A / legacy-integration evidence.

Support requires at least two independent support classes with no caution class. One mixed or isolated directional class is caution. Two or more caution classes remain caution/alert. No downstream directional evidence remains unknown.

## Held-out evaluation

Expected label and expected alert are not inputs to classification. Classification runs first. The already-produced observation is then compared with held-out expectation.

Acceptance decisions:

```text
false negative > 0   -> REJECT
label mismatch > 0   -> REJECT
false positive > 0   -> REVIEW
otherwise            -> ACCEPT
```

Labels:

```text
support
caution
reject
unknown
```

## Boundary

This Canary does not:

- infer revenue from deployments;
- infer integration success from acquisition close alone;
- bypass the applicability guard;
- convert contradictory evidence into support;
- authorize provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action.
