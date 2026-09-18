# OrderScope — W1-001 Live Canary Change-Window Report

Status: **ROLLED_BACK — cadence blocker requires code repair and review**
Date: 2026-09-11 JST
Task: `W1-001 — Worker/Schedule News metadata acquisition Live Canary`
Release commit: `30542ffaf3943bec91a6a6543e07df00432e1492`
Branch: `docs/mermaid-conventions-v0.1`
Environment: `live-canary`
Runbook: `W1-001_LIVE_CANARY_CHANGE_WINDOW_RUNBOOK_2026-09-11.md`
Checklist: `W1-001_LIVE_CANARY_ACCEPTANCE_CHECKLIST_2026-09-11.md`

## 1. Decision

The W1-001 live Canary was opened twice and rolled back twice. The final remote
state is safe:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
NEWS_ACQUISITION_CADENCE_MINUTES=5
Cron=* * * * *
```

The final decision is `ROLLED_BACK`. The Canary is not accepted and no
`full-v0.1` activation is authorized.

## 2. Preflight evidence

The reviewed release and local boundary passed before remote mutation:

```text
full TypeScript suite       -> 126 passed
TypeScript typecheck        -> passed
Wrangler live-canary dry-run -> passed
git diff --check            -> passed
working tree before window  -> clean
```

Remote preflight confirmed:

- `STATE_DB` resolved to `orderscope-state-live-canary`
  (`03c85865-1aa3-4b0c-b219-18987cd260a6`);
- the only pending migration was reviewed `0007_news_metadata.sql`;
- both required managed secret names existed;
- the pre-window Worker was `shadow` with News disabled;
- the existing Cron remained one minute.

No secret values, authentication headers, News bodies, or raw provider response
bodies were captured in this report.

## 3. D1 migration result

`0007_news_metadata.sql` was applied successfully to the live-canary D1 database.
Post-apply verification confirmed:

```text
news_article
news_query_membership
news_checkpoint
```

Existing representative Market tables remained present:

```text
normalized_bar
coverage_checkpoint
latest_digest
```

Wrangler subsequently reported no pending migrations. The additive News schema
remains applied after rollback; no destructive reverse migration was attempted.

## 4. Deployment and activation timeline

All timestamps below are UTC. Add nine hours for JST.

| Time | Version | Event | Result |
|---|---|---|---|
| 2026-09-10 19:15:47 | `232685fa-5d46-4791-9f5f-c94597f75924` | Reviewed build deployed in `shadow`, News disabled | Healthy |
| 2026-09-10 19:17:53 | `74d79f9e-d077-4e57-bc36-3bbd0074a18b` | First live AMD/NVDA News activation | Scheduled invocation failed before acquisition |
| 2026-09-10 19:20:44 | `c5c59b07-da7c-4805-9d11-095344a68a52` | First rollback | `shadow`, News disabled |
| 2026-09-10 19:39:52 | `3431873e-11d2-46f8-86b4-3aef83511dc1` | Activation resumed after secret update | First live tick completed safely; News did not plan |
| 2026-09-10 19:48:24 | `c2aebaa7-d82a-4f79-986a-5700b01a5146` | Final rollback | Healthy `shadow`, News disabled |

The pre-window deployment recorded before these changes was
`619c0b2b-5cb0-4351-80a8-e854c0958897`.

## 5. First stop — Alpaca authentication

The first activated scheduled invocation raised:

```text
AlpacaMarketCalendarProvider.getCalendar
alpaca market calendar failed: 401
```

Because the scheduled path could not establish Market health or reach News
acquisition, the Worker was immediately returned to `shadow` with News disabled.
The local `.env` credential pair was then uploaded as the two managed
live-canary secrets without exposing their values. A direct metadata-free status
check against the Alpaca calendar endpoint returned HTTP 200, resolving this
first blocker.

## 6. Second stop — News cadence cannot become eligible

After the credential update, the second activation produced a successful live
scheduled digest at `2026-09-10T19:40:15.000Z`:

```text
Market jobs completed       -> 1
Market outcome              -> SUCCEEDED
Market pages                -> 1
Market inserted bars        -> 100
Market conflicts/rejections -> 0 / 0
total external subrequests  -> 1 / 40
total D1 queries            -> 21 / 40
withinBudget                -> true
```

News remained active in configuration but planned zero jobs. The live evidence
showed eight consecutive Cron timestamps ending in `:15.000Z`, including the
nominal five-minute boundary at `19:40:15Z`.

The current planner in `src/news-schedule.ts` requires:

```text
scheduledTime milliseconds modulo cadence milliseconds == 0
```

Consequently, a stable 15-second Cron offset never satisfies the five-minute
eligibility test. Leaving the Canary active would collect no News evidence and
could not satisfy the acceptance checklist's 12 eligible opportunities. The
runbook requires a stop when a different technical delta is necessary, so the
Worker was rolled back without changing the Cron or adding an unreviewed code
fix.

## 7. Rollback verification and final state

Final Worker version:

```text
c2aebaa7-d82a-4f79-986a-5700b01a5146
```

Verified bindings and health:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
STATE_DB=orderscope-state-live-canary
health.ok=true
health.status=shadow
News planned/selected/completed/failed=0/0/0/0
```

The checked-in `wrangler.jsonc` was also restored to the safe baseline. No
runtime variable other than the reviewed activation pair was changed during the
window, and the Cron remained unchanged.

## 8. Acceptance checklist disposition

```text
Authorization/release identity -> satisfied
Local validation               -> satisfied
D1 migration                   -> satisfied
Secret-name boundary           -> satisfied
Alpaca credential status       -> repaired; HTTP 200 after update
Deployment/health              -> satisfied after rollback
First completed live budget    -> external 1/40; D1 21/40
Eligible News opportunities    -> 0; failed
News correctness/lag evidence  -> not exercised / inconclusive
Final decision                 -> ROLLED_BACK
```

No combined budget crossing, News body persistence, secret leakage, unexpected
symbol expansion, checkpoint advancement, or schema corruption was observed.
Because News never became eligible, these observations do not constitute News
Canary acceptance.

## 9. Required repair before reopening

Before another live change window:

1. change News cadence eligibility to use a reviewed minute bucket or equivalent
   rule that is insensitive to the scheduler's seconds offset;
2. add focused tests for non-zero scheduled seconds at eligible and ineligible
   five-minute boundaries;
3. rerun the full suite, typecheck, Wrangler dry-run, and diff checks;
4. obtain code review/acceptance for the changed technical delta;
5. redeploy in `shadow` with News disabled and verify scheduled health;
6. open a new reviewed activation window and collect at least 12 eligible News
   opportunities unless a hard-stop condition occurs first.

Do not reopen the live Canary from configuration alone while the cadence blocker
remains.
