# UWBS-086 — 2024-08-05 Historical Replay Runner Local Acceptance — 2026-09-27

Status: **ACCEPTED**
Branch: `l1-003-local-market-recovery`

## Scope

This acceptance covers the deterministic historical replay runner that classifies the repository-backed 2024-08-02..2024-08-08 packet without consulting its held-out expected label during classification.

## Local verification

```text
historical replay runner:     9 passed
historical manifest:          9 passed
historical packet contract:   9 passed
full Python regression:      808 passed
compileall:                  PASS
git diff --check:            PASS
```

## Accepted boundary

- classification reads only classifier-input lanes;
- expected regime/alert evidence is consulted only when building the Canary comparison result;
- the 2024-08-05 packet independently produces a Risk-Off classification from multiple signal classes;
- look-ahead protection for crypto-derivatives evidence remains preserved;
- this acceptance does not constitute final UWBS-086 historical-capacity acceptance.

## Next step

Connect historical replay results to aggregate false-positive / false-negative / regime-mismatch accounting, while keeping capacity assessment as a separate second-stage input.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution or trading action was performed.
