# OrderScope — L1-003 NVDA Historical Recovery Change Window

Status: **ACCEPTED — first remote NVDA recovery chunk completed and gate removed**
Date: 2026-09-16 JST
Environment: `live-canary`
Parent: `L1-003_PHASE_B_PREREQUISITE_MARKET_RECOVERY_SCHEDULE_2026-09-16.md`

## 1. Purpose and boundary

Recover one bounded NVDA Regular-session chunk from the persisted September 2
checkpoint. This is prerequisite recovery evidence, not Phase B evidence.

This document does not authorize deploy, Worker/Cron/config changes, provider
execution, or D1 writes. The Worker remains Shadow and News remains disabled.

## 2. Stage 1 read-only evidence

Captured at `2026-09-16T08:00:24.138Z`:

```text
repository HEAD              c3a27f2af89beb889f944fe08cfa10f0f726d1b1
worktree                     dirty; recovery implementation is not committed/deployed
Cloudflare account           905a2bdec98321c41ac41e48b2fff501
D1 database                  orderscope-state-live-canary
D1 database id               03c85865-1aa3-4b0c-b219-18987cd260a6
D1 control path              PASS; changes=0; rows_written=0
Worker mode                  shadow
News                         disabled
feed                         iex
Universe profile             canary-v0.1
Universe revision            stock-monitoring-canary-v0.1
calendar range               [2026-09-02, 2026-09-17)
calendar revision            alpaca-calendar-v2:da7d32f3
authoritative sessions       10 Regular sessions
last completed session       2026-09-15T20:00:00.000Z
```

The calendar was retrieved through the checked-in
`AlpacaMarketCalendarProvider`; no weekday or UTC-session inference was used.

## 3. Frozen candidate and recovery request

NVDA is selected because its checkpoint is `COMPLETE`, contains no missing
ranges, and is at the authoritative September 2 Regular close. SPY is complete
but mid-session; AMD and QQQ are excluded because they are `PARTIAL`.

```text
recovery_id                  L1-003-NVDA-20260916-01
provider_revision            alpaca-stock-bars-v1
coverage_key                 NVDA|1Min|REGULAR|stock:iex:raw
instrument                   NVDA / 1Min / alpaca_stock_bars
session_scope                REGULAR
logical_data_variant         stock:iex:raw
mode                         CATCH_UP
recovery_start               2026-09-02T20:00:00.000Z
recovery_end                 2026-09-15T20:00:00.000Z
checkpoint_state             COMPLETE
checkpoint_complete_through  2026-09-02T20:00:00.000Z
checkpoint_missing_ranges    []
checkpoint_version           6
max_jobs                     1
max_pages                    10
max_bars                     100
external ceiling             40
D1 ceiling                   40
```

The first deterministic job is:

```text
job_id                       historical-market-recovery:ef94f87d37bf2746
requested_start              2026-09-03T13:30:00.000Z
requested_end                2026-09-03T15:10:00.000Z
expected bars                100
expected checkpoint version  6
```

## 4. Mandatory execution sequence

Before any mutation, re-run the read-only preflight and require exact equality
for account, database, mode, News state, feed, Universe revision, calendar
revision, coverage identity, state, complete-through, missing ranges, and
checkpoint version.

Then:

```text
preflight equality PASS
  -> run exactly one historical-recovery chunk
  -> require withinBudget=true
  -> inspect acquisition attempt and acceptance counts
  -> re-read checkpoint and unresolved evidence
  -> stop; do not automatically plan or execute the next chunk
```

Successful evidence requires:

```text
outcome=SUCCEEDED
pages <= 10
inserted + matched = 100
conflicts=0
rejected=0
missing=0
checkpoint complete_through=2026-09-03T15:10:00.000Z
checkpoint state=COMPLETE
checkpoint missing_ranges=[]
checkpoint version=7
control path PASS
Worker shadow / News disabled
```

## 5. Stop conditions

Stop before execution on any preflight drift. Stop after execution on PARTIAL,
FAILED, missing, conflict, rejection, budget failure, CAS conflict, provider
throttling requiring wider limits, control-path failure, or unexplained
checkpoint movement. Do not retry or run a second chunk in the same window.

## 6. Locally accepted one-shot invocation path

The Worker now contains the fixed endpoint
`POST /control/historical-recovery/nvda/first-chunk`. It is fail-closed behind
`HISTORICAL_RECOVERY_ENABLED=false` and requires the separately provisioned
`HISTORICAL_RECOVERY_CONTROL_TOKEN` Bearer secret. The caller must also supply
the exact frozen recovery and job identities in
`x-orderscope-recovery-id` and `x-orderscope-job-id`.

The handler independently requires Shadow mode, News disabled, the reviewed
feed/profile/bounds, exact checkpoint identity/version/range, and the exact
calendar revision. It acquires the existing D1 lease, executes through the
normal acquisition executor, verifies the 100-bar success contract and
checkpoint version 7, then stops. A replay fails checkpoint preflight before a
provider request.

Local acceptance on 2026-09-16:

```text
focused recovery/control tests     20 passed
full TypeScript suite              passed
TypeScript typecheck               passed
wrangler generated-type check      passed
live-canary deploy dry-run          passed
git diff check                      passed
remote writes                       none
```

## 7. Remote execution evidence

The reviewed commit `ed9363d3ae548c470d256770a49f809420660a80` was
pushed before the change window. The 2026-09-16 window then completed this
sequence:

```text
09:28Z  read-only preflight PASS; checkpoint version 6 unchanged
09:29Z  endpoint deployed with HISTORICAL_RECOVERY_ENABLED=false
09:29Z  disabled endpoint returned 404
09:30Z  temporary gate deployed; unauthenticated request returned 401
09:30Z  exactly one authenticated frozen request returned HTTP 200
09:30Z  false-gate configuration restored; endpoint returned 404
09:31Z  temporary control secret deleted
```

Invocation result:

```text
accepted                       true
outcome                        SUCCEEDED
job_id                         historical-market-recovery:ef94f87d37bf2746
pages                          1
inserted / matched             100 / 0
conflicts / rejected / missing 0 / 0 / 0
external subrequests           1 of 40
D1 queries                     15 of 40
stopped_after_one_chunk        true
```

Independent read-only D1 verification found one SUCCEEDED acquisition attempt,
100 INSERTED acceptance receipts, and 100 canonical NVDA bars from
`2026-09-03T13:30:00.000Z` through `2026-09-03T15:09:00.000Z`. The checkpoint
is now `COMPLETE`, has no missing ranges, is complete through
`2026-09-03T15:10:00.000Z`, and is version 7. The verification statements made
zero writes and the control path remained healthy.

Final safety state at `2026-09-16T09:37:15Z`:

```text
deployment                     86c12b2d-408e-4ebb-95b0-659edae27e04
Worker mode                    shadow
News                           disabled
HISTORICAL_RECOVERY_ENABLED    false
control endpoint               404
control secret                 deleted
```

## 8. Next gate

This acceptance authorizes no automatic second chunk. The frozen endpoint now
fails checkpoint preflight because version 6 has advanced to version 7. The
next action is a separately reviewed continuation design/change window that
freezes the version-7 checkpoint and next deterministic chunk, or replaces the
single-use endpoint with an equally bounded reviewed continuation mechanism.
Direct D1 checkpoint edits, ad-hoc bar inserts, and Phase B activation remain
prohibited.
