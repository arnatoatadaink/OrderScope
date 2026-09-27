# UWBS-092 Local Acceptance — 2026-09-27

Status: **ACCEPTED**

Scope: Physical-SaaS classifier / applicability guard.

## Verification

```text
focused tests:      10 passed in 3.02s
full regression:    894 passed in 46.00s
compileall:         PASS
git diff --check:   PASS
```

## Accepted boundary

The applicability guard classifies whether the Physical-SaaS analysis lane may be applied to a subject without silently treating hardware shipment, ARR-like commercial metrics, or acquisition activity as sufficient evidence by themselves.

Accepted outcomes:

```text
applicable
conditional
not_applicable
unknown
```

`applicable` requires physical deployment evidence together with recurring-service / recurring-revenue evidence. Contradicting evidence prevents the downstream gate from opening automatically.

This acceptance does not authorize live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action.
