# UWBS-086 — Final Shadow Capacity Acceptance — 2026-09-27

Status: **ACCEPTED — CURRENT CHECKED-IN SHADOW RUNTIME ONLY**
Branch: `l1-003-local-market-recovery`

## Local verification

```text
shadow capacity bound focused tests:      10 passed in 3.36s
D1 capacity evidence focused tests:       10 passed in 2.04s
historical Canary evaluation tests:        7 passed in 2.35s
full Python regression:                  835 passed in 45.95s
compileall:                              PASS
git diff --check:                        PASS
```

## Historical Canary acceptance

Repository-backed historical packet: `analysis/config/cross_market/uwbs-086-2024-08-05-risk-off-v0.1.json`

```text
expected_regime:      risk_off
observed_regime:      risk_off
expected_alert:       true
observed_alert:       true
false positives:      0
false negatives:      0
regime mismatches:    0
historical clean:     true
```

## Current checked-in runtime boundary

```text
WORKER_MODE=shadow
UNIVERSE_PROFILE=canary-v0.1
ACQUISITION_MAX_JOBS_PER_TICK=2
ACQUISITION_MAX_PAGES_PER_JOB=10
ACQUISITION_MAX_BARS_PER_JOB=100
NEWS_ACQUISITION_ENABLED=false
cron=* * * * *
```

Because the checked-in Worker is in shadow mode, the scheduled tick does not execute market acquisition jobs. When STATE_DB is available it persists the market digest through `D1LatestDigestStore.put()`.

The digest store uses three D1 statements per tick:

1. upsert one `latest_digest` row;
2. insert/upsert one `digest_history` row;
3. delete `digest_history` rows outside the newest 96 rows.

`digest_history` has a primary key on `(digest_key, generated_at)` and an index on `(digest_key, generated_at DESC)`.

## Conservative shadow projection

The accepted shadow bound applies a 1.25x safety multiplier and includes index-write effects in the conservative write bound.

```text
Worker requests/day:       1,440
D1 rows read/day:        720,000
D1 rows written/day:      14,400
storage warm-up:        1,986,560 bytes
```

Against the external planning envelope used for this acceptance:

```text
Worker requests/day limit: 100,000
D1 rows read/day limit:   5,000,000
D1 rows write/day limit:    100,000
```

Headroom:

```text
Worker requests: 98.56%
D1 rows read:    85.60%
D1 rows written: 85.60%
```

The minimum accepted headroom is therefore 85.60%, well above the OrderScope 20% guard.

## R0-007 billing evidence classification

Existing repository/local evidence:

```text
rows_read:      3906
rows_written:   0
size_after:     4,796,416 bytes
changed_db:     false
returned rows:  1
```

Two independent R0-007 custody reads produced the same billing values. This is accepted as specific read-query evidence only. It is not a representative scheduled Worker invocation and is not multiplied by 1,440/day for normal Cron capacity.

## Final decision

```text
Historical Canary:                 ACCEPT
Current checked-in shadow capacity: ACCEPT
UWBS-086 current shadow boundary:   ACCEPT
```

## Explicit exclusions

This acceptance does **not** authorize or accept future `WORKER_MODE=live` acquisition capacity.

Live mode uses market checkpoint reads/writes, leases, acquisition attempts, bar acceptance/storage, optional scheduler run evidence, and digest persistence. Its D1 billing rows must be measured or defensibly bounded separately before live capacity acceptance.

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution, paid procurement, or trading action was performed for this acceptance.

If `WORKER_MODE`, cron frequency, digest retention/indexing, news enablement, acquisition limits, or D1 schema materially change, this shadow capacity acceptance must be re-evaluated.
