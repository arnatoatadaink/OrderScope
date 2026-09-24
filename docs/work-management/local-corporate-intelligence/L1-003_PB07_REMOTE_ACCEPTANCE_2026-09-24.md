# OrderScope — L1-003 PB-07 Stability Observation Remote Acceptance

Status: **ACCEPTED REMOTELY — PB-08 next**
Date: 2026-09-24 JST
Environment: `live-canary`

## Final acceptance evidence

```text
final_checkpoint_ok       1
canonical_bars            199
clean_nvda_attempts       2
bad_nvda_attempts         0
clean_live_digests        2
nonclean_market_summaries 0
```

Final NVDA checkpoint:

```text
coverage key        NVDA|1Min|REGULAR|stock:iex:raw
version             61
complete through    2026-09-23T18:28:00.000Z
source observed     2026-09-23T18:28:00.000Z
state               COMPLETE
missing ranges      []
blocker             null
retry_not_before    null
unresolved attempts 0
```

Accepted normal-scheduler executions:

```text
2026-09-24T14:39:23Z
  request  2026-09-23T15:09:00Z -> 2026-09-23T16:49:00Z
  result   SUCCEEDED
  inserted 99
  matched  1
  conflicts/rejected/missing 0
  checkpoint v60 / 16:49Z
  budget withinBudget=true

2026-09-24T14:40:23Z
  request  2026-09-23T16:48:00Z -> 2026-09-23T18:28:00Z
  result   SUCCEEDED
  inserted 99
  matched  1
  conflicts/rejected/missing 0
  checkpoint v61 / 18:28Z
  budget withinBudget=true
```

No NVDA FAILED/PARTIAL/unresolved attempt occurred between the two accepted
normal-scheduler executions. The combined frozen interval contains 199
canonical one-minute bars as expected.

## Safe close

Final deployed baseline is:

```text
WORKER_MODE              shadow
PREDICTION_MODE          shadow
ALPACA_FEED              iex
UNIVERSE_PROFILE         canary-v0.1
NEWS_ACQUISITION_ENABLED false
HISTORICAL_RECOVERY_ENABLED false
Cron                     * * * * *
```

PB-07 is complete.

## Critical path

```text
PB-04 COMPLETE
PB-05 ACCEPTED
PB-06 ACCEPTED
PB-07 ACCEPTED
PB-08 NEXT
PB-09 GATED
PB-10 NOT AUTHORIZED
```

PB-08 must freeze the Phase B entry packet. This acceptance record does not
authorize a pause/resume experiment or any Phase B mutation.
