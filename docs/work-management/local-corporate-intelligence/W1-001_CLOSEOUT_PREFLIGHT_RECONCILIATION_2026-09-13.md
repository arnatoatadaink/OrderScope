# OrderScope — W1-001 Closeout Preflight Reconciliation

Status: **READY — market-day/live-authorization gated**
Date: 2026-09-13 JST
Branch: `docs/mermaid-conventions-v0.1`
Scope: W1-001 short confirmation/closeout Canary preflight only

## 1. Observed preflight result

The 2026-09-13 read-only preflight passed the local and Cloudflare control-path checks required before a new live-canary window:

- TypeScript full suite: 178/178 passed;
- TypeScript typecheck: passed;
- Cloudflare type generation: passed;
- `wrangler deploy --dry-run --env live-canary`: passed;
- target D1 binding: `orderscope-state-live-canary`;
- Worker dry-run state: `WORKER_MODE=shadow`;
- News dry-run state: `NEWS_ACQUISITION_ENABLED=false`;
- Universe: `canary-v0.1`;
- News cadence: 5 minutes;
- News symbols: AMD/NVDA;
- required secret names present: `ALPACA_API_KEY`, `ALPACA_API_SECRET`;
- remote `SELECT 1`: passed;
- remote `PRAGMA table_list`: passed;
- no `7403`, quota error, binding error, or control-path stall observed;
- deployed `/health`: `ok=true`, `mode=shadow`, News disabled.

## 2. Pending migration reconciliation

`wrangler d1 migrations list STATE_DB --remote --env live-canary` reports:

```text
0008_scheduler_run_evidence.sql
```

as pending.

This is a known, reviewed, separately gated migration. It is **not required for the W1-001 confirmation/closeout Canary while scheduler run evidence remains disabled**.

Current Worker behavior is fail-safe at this boundary:

- `SCHEDULER_RUN_EVIDENCE_ENABLED` is optional;
- when absent, the runtime defaults it to `false`;
- when disabled, the Worker selects `DISABLED_RUN_EVIDENCE_STORE` rather than D1-backed scheduler evidence;
- therefore the W1-001 closeout Canary does not require the `scheduler_run` / `scheduler_run_job` tables introduced by migration `0008`.

The migration remains **not authorized for remote application** by this reconciliation. It must stay a separate change-control item.

## 3. Go / No-Go decision

The preflight is accepted as:

```text
W1-007 Web review              = Accepted
W1-001 read-only preflight     = Passed
0008 pending migration         = Known gated exception; do not apply
W1-001 short closeout Canary   = Ready
live mutation authorization    = Still required
market-day evidence gate       = Still required
```

The pending `0008` migration is therefore no longer treated as an unexpected blocker for this specific closeout window, provided `SCHEDULER_RUN_EVIDENCE_ENABLED` remains unset/false for the entire window.

## 4. Closeout-window constraints

The next live window must preserve all of the following:

```text
environment = live-canary
UNIVERSE_PROFILE = canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS = AMD,NVDA
NEWS_ACQUISITION_CADENCE_MINUTES = 5
Cron = * * * * *
SCHEDULER_RUN_EVIDENCE_ENABLED = false / unset
migration 0008 = not applied
```

Only the reviewed activation pair may change during the approved window:

```text
WORKER_MODE=live
NEWS_ACQUISITION_ENABLED=true
```

The closeout purpose is limited to confirming control-path continuity during live execution and proving safe rollback after a short observation window. It is not a production rollout.

## 5. Required evidence during the short closeout

Observe three distinct eligible five-minute News opportunities unless a hard-stop condition occurs first.

For each opportunity retain only operational metadata:

- scheduled timestamp;
- Market and News planned/selected/completed/failed counts;
- external subrequest count;
- D1 query count;
- `withinBudget` result;
- News article/duplicate counts if any;
- Market regression indicators;
- Worker exception/resource indicators.

During the same live window, at least one read-only D1/control-path probe must succeed. A second read-only probe should succeed before rollback/closeout is declared complete.

## 6. Hard-stop conditions

Rollback immediately if any of the following occurs:

- Cloudflare API `7403` or equivalent control-path authorization loss;
- D1/control-path request stalls such that monitoring is no longer reliable;
- external or D1 budget crossing;
- Market regression attributable to News activation;
- News checkpoint false completion after provider failure;
- unauthorized symbol/config expansion;
- secret or News body leakage;
- any requirement to apply migration `0008` or enable scheduler-run evidence to continue the window.

## 7. Final boundary

This document does not authorize live activation by itself. It reconciles the pending migration and moves W1-001 to **Ready / market-day and explicit-authorization gated**.

Remote application of `0008_scheduler_run_evidence.sql`, scheduler-evidence activation, `SMOKE-007`, D1 export/purge, full-v0.1 activation, and Cron changes remain outside this window.
