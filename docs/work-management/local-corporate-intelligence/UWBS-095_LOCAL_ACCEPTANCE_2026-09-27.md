# UWBS-095 — Local Acceptance

Status: **ACCEPTED**
Date: 2026-09-27

Scope: VIX futures term-structure Derived Metrics only.

## Local verification

```text
focused UWBS-095 tests: 10 passed in 2.65s
full Python regression: 924 passed in 33.55s
compileall: PASS
git diff --check: PASS
```

## Accepted boundary

The implementation keeps source futures observations separate from deterministic term-structure metrics. Accepted Derived Metrics include front/second spread, front/second ratio, and curve-shape classification (`contango`, `backwardation`, `flat`).

No VIX-linked ETP roll yield, decay, convergence return, fear/risk-off regime, or causal attribution is accepted by this task.

## Runtime exclusions

PB-09/PB-10 remain parked and not authorized. No live provider activation, Worker/Cron mutation, D1 mutation, paid procurement, or trading action is authorized by this acceptance.
