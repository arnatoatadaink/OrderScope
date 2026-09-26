# L1-003 PB-08 resumption readiness

Status: **REMOTE READY / NEW WINDOW AUTHORIZATION REQUIRED**

## Resume point

Remote branch fast-forwarded to `a186bf8`. No live mutation was executed during
the interrupted run or this readiness preparation. PB-06/PB-07 and the accepted
provider-absence acknowledgement evidence remain accepted under the moving
retention runbook; they do not need calendar-day repetition.

## Fresh read-only evidence

- Wrangler 4.127.1: existing OAuth identity confirmed; D1 `auth_ok=1`.
- Snapshot: `2026-09-26T07:11:42.000Z`, `remoteMutation=false`.
- Worker shadow, News disabled, IEX; historical recovery endpoint HTTP 404.
- NVDA v61 COMPLETE, completeThrough/sourceObservedThrough
  `2026-09-23T18:28:00.000Z`.
- AMD v43 through `2026-09-24T14:50:00.000Z`.
- QQQ v12 through `2026-09-24T14:33:00.000Z`.
- SPY v44 through `2026-09-24T15:10:00.000Z`.
- BTCUSD v49 through `2026-09-24T08:13:00.000Z`.
- All five checkpoints COMPLETE, missing=[], blocker=null, retry_not_before=null.
- NVDA unresolved attempts=0; recent NVDA attempts SUCCEEDED.
- Latest market digest at snapshot: `2026-09-26T07:11:19.000Z`, shadow.

Read-only AlpacaMarketCalendarProvider observation at
`2026-09-26T07:13:35.738Z`, revision `alpaca-calendar-v2:60e16a67`, confirms
Sep25 REGULAR open `13:30Z`, close `20:00Z`; next session Sep28.

Configured retention is 1440 minutes. Snapshot floor is
`2026-09-25T07:11:42.000Z`; Sep25 is closed and fully retained. The existing
Sep25 exact-close geometry remains valid; earlier accepted work is preserved.

## Concrete PB-08 window

- Entry: NVDA v61 / `2026-09-23T18:28:00.000Z`.
- Target: NVDA v65 / `2026-09-25T20:00:00.000Z`, exact close.
- Four clean jobs; accepted totals (inserted + matched): 100,100,100,93.
- Maximum 16 normal scheduler opportunities; existing cron/universe/priority.
- Guard: retention floor must not pass `2026-09-25T13:30:00.000Z`.
- Packet expires after `2026-09-26T13:30:00Z` (22:30 JST), or earlier upon
  checkpoint, competition, blocker, configuration, or unresolved-attempt drift.
- Final coverage/sourceObservedThrough equal target; COMPLETE, missing=[],
  blocker=null, retry_not_before=null; all NVDA attempts finished SUCCEEDED,
  conflicts/rejected/missing=0, version=61+accepted attempt count.
- Safe close restores checked-in shadow deployment and verifies News disabled,
  IEX and closed temporary controls; no temporary secret is required.

## Local acceptance and execution environment

Use Linux Node via `/home/y/.nvm/versions/node/v24.21.0/bin` on PATH.
The initial sandboxed Node test run reported file-level results only. The
normal WSL run verified 34 actual test cases, 34 pass, zero fail, and typecheck
PASS. Bash syntax and git diff checks passed. The competition test now freezes
the fresh observation/floor above. The acceptance script's stale Sep24 target
display was corrected to Sep25.

## Authorization boundary / remaining work

This document records readiness, not authorization. The runbook requires an
explicit authorization identifying this newly observed PB-08 Sep25 exact-close
window before temporary live deployment. After authorization, run the bounded
window, capture exact final evidence, safe-close, and record PB-08 acceptance.
PB-09 requires a separate reviewed Phase B window and PB-10 pause/resume remains
outside this packet.
