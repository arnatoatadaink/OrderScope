# UWBS-085 Local Acceptance — 2026-09-27

Status: **ACCEPTED**

## Evidence

```text
cross-asset regime focused tests: 9 passed
full Python regression:          762 passed
compileall:                      PASS
git diff --check:                PASS
```

Accepted boundary:

- broad Risk-On cannot be established from a single BTC/ETF/oil signal;
- `SUPPORT` requires at least three independent signal classes;
- `PARTIAL` requires at least two independent signal classes;
- broad Risk-On requires traditional-risk evidence plus cross-asset confirmation;
- Crypto Risk-On requires crypto-market evidence plus ETF-flow or derivatives confirmation;
- contradictory and unknown states remain explicit.

No live provider activation, Worker/Cron mutation, D1 mutation, paid procurement, or trading action occurred.

Next canonical task: `UWBS-086 — Oil/BTC cross-asset Canary and Worker/D1 capacity acceptance`.
