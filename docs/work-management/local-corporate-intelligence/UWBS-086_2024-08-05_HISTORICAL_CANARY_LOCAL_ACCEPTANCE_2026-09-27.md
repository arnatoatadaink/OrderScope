# UWBS-086 — 2024-08-05 Historical Canary Local Acceptance — 2026-09-27

Status: **ACCEPTED — HISTORICAL CANARY EVALUATION**
Branch: `l1-003-local-market-recovery`

## Local verification

```text
historical Canary evaluation focused tests: 7 passed in 2.86s
historical replay runner focused tests:     9 passed in 2.67s
full Python regression:                   815 passed in 45.17s
compileall:                               PASS
git diff --check:                         PASS
```

## Accepted historical result

Repository-backed packet:

`analysis/config/cross_market/uwbs-086-2024-08-05-risk-off-v0.1.json`

Held-out expected label:

```text
expected_regime: risk_off
expected_alert:  true
```

Independent replay result:

```text
observed_regime: risk_off
observed_alert:  true
```

Historical Canary summary:

```text
false positives:    0
false negatives:    0
regime mismatches:  0
historical clean:   true
```

The expected label remains independent of classifier-input evidence. The replay runner classifies the packet first and only then compares the result with the held-out label.

## Remaining UWBS-086 boundary

Historical Canary evidence is accepted for the first bounded packet, but UWBS-086 final acceptance remains open pending Worker/D1 capacity evidence.

Required capacity evidence:

- Worker requests/day projection;
- D1 rows read/day from measured or defensibly bounded D1 metadata;
- D1 rows written/day from measured or defensibly bounded D1 metadata;
- D1 storage growth/day;
- capacity headroom against a fresh external platform envelope.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution or trading action was performed for this acceptance.
