# OrderScope — W1-001 Confirmation / Closeout Change-Window Report

Status: **ACCEPTED — confirmation evidence collected and safe rollback verified**
Date: 2026-09-14 JST
Task: `W1-001 — short monitored AMD/NVDA News Canary confirmation/closeout`
Release commit: `56ee745ebf579ddb744d7113afce776192862473`
Branch: `docs/mermaid-conventions-v0.1`
Environment: `live-canary`
Change window: `W1-001_CONFIRMATION_CLOSEOUT_CHANGE_WINDOW_2026-09-13.md`

## 1. Final disposition

The short reviewed AMD/NVDA metadata-only News Canary completed three distinct
eligible five-minute opportunities. Each opportunity planned, selected, and
completed one News job with no partial or failure. Ineligible minutes produced
no phantom News work. All reviewed invocations remained inside the shared
external and D1 ceilings, and the Cloudflare D1 control path succeeded during
and after the active window without recurrence of API error `7403`.

The checked-in safe baseline was deployed immediately after the third eligible
opportunity. The final Worker version is
`f6b35356-a7c2-40ed-8bbb-7b957f4ead11`, with:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
NEWS_ACQUISITION_CADENCE_MINUTES=5
Cron=* * * * *
```

The final disposition is `ACCEPTED`. This closes the bounded W1-001
confirmation window; it does not authorize `full-v0.1`, continuous Live mode,
Cron changes, scheduler-evidence activation, `SMOKE-007`, remote D1 purge,
backup/restore, or additional migrations.

## 2. Release and pre-window evidence

The handoff recorded the following completed acceptance before the remote
window:

```text
focused TypeScript       -> 1 passed / 0 failed
full TypeScript          -> 179 passed / 0 failed
typecheck                -> passed
git diff                 -> clean
deploy:check live-canary -> passed
remote SELECT 1          -> passed
remote PRAGMA table_list -> passed
activation dry-run       -> passed
```

When monitoring resumed, the operator activation had already completed. The
active deployment was therefore identified through deployment history and
confirmed independently through `/health` before further mutation. The version
immediately preceding activation was
`16af6aeb-6818-4a09-be58-10aa7931a2de`; this is a history-derived pre-window
version, rather than a value captured again before the activation command.

The first observed active state was healthy:

```text
activation version: 2907cd45-7d7b-446e-99ca-b1f6b1a2d674
deployment created: 2026-09-14T12:41:00.623Z
/health mode: live
/health News mode: active
control_path_ok: 1
```

## 3. Deployment timeline

| UTC time | JST time | Version | Event | Result |
|---|---|---|---|---|
| 2026-09-14 12:41:00.623 | 2026-09-14 21:41:00.623 | `2907cd45-7d7b-446e-99ca-b1f6b1a2d674` | Confirmation activation | Reviewed pair active |
| 2026-09-14 12:50:58 | 2026-09-14 21:50:58 | same | First counted eligible opportunity | News `1/1/1/0` |
| 2026-09-14 12:55:58 | 2026-09-14 21:55:58 | same | Second counted eligible opportunity | News `1/1/1/0` |
| 2026-09-14 13:00:58 | 2026-09-14 22:00:58 | same | Third counted eligible opportunity | News `1/1/1/0` |
| 2026-09-14 13:01:58.014 | 2026-09-14 22:01:58.014 | `f6b35356-a7c2-40ed-8bbb-7b957f4ead11` | Safe-baseline rollback | Shadow; News disabled |
| 2026-09-14 13:02:58 | 2026-09-14 22:02:58 | same | Post-rollback scheduled invocation | News `0/0/0/0` |

The tail was attached after activation. The earlier `12:45` opportunity was not
counted because it was not directly observed in the attached tail.

## 4. Per-opportunity evidence

| Scheduled UTC | News planned / selected / completed / failed | Pages | Observed / duplicate / updated | External / 40 | D1 / 40 | Within budget | Worker |
|---|---:|---:|---:|---:|---:|---|---|
| `12:50:58` | `1 / 1 / 1 / 0` | 2 | `3 / 3 / 0` | `2 / 40` | `15 / 40` | true | Ok |
| `12:55:58` | `1 / 1 / 1 / 0` | 2 | `1 / 1 / 0` | `2 / 40` | `12 / 40` | true | Ok |
| `13:00:58` | `1 / 1 / 1 / 0` | 2 | `0 / 0 / 0` | `2 / 40` | `9 / 40` | true | Ok |

The retained tick digest does not expose separate News inserted/conflict fields.
All four observed article results were classified as duplicates, no update was
reported, and no new-identity or conflict signal appeared. No article arrival
was required for this confirmation window.

Observed ineligible ticks at `12:47:58`, `12:48:58`, `12:49:58`,
`12:51:58` through `12:54:58`, and `12:57:58` through `12:59:58` consistently
reported News `planned/selected/completed/failed=0/0/0/0`. Their normal totals
were `external=0` and `D1=7`, with `withinBudget=true`.

At `12:56:58`, one existing Market `MISSING_RANGE` retry returned `PARTIAL`
with `matched=1`, `missing=2`, `conflicts=0`, and `rejected=0`. It retained the
unresolved gap, used `external=1/40` and `D1=21/40`, and completed with Worker
outcome `Ok`. This matches the previously accepted fail-closed Market gap-retry
behavior. No Market failure, false coverage advance, or News-attributable Market
regression was observed.

Across the reviewed tail:

```text
eligible opportunities            -> 3 distinct
News planned / completed / failed -> 3 / 3 / 0
News partial                      -> 0
News pages                        -> 6
article observations / duplicates -> 4 / 4
normal external/tick              -> 2
max external/tick                 -> 2 / 40
eligible D1/tick                  -> 9–15 / 40
max D1/tick                       -> 21 / 40 (Market gap retry)
withinBudget                      -> true for every reviewed tick
```

Every tailed invocation had `outcome=ok`, an empty exception list, and no
diagnostic resource event. No CPU/resource-exceeded, repeated exception, 429,
5xx, unauthorized symbol, News body, credential, or authentication-header
leakage was observed. The configured symbol boundary remained AMD/NVDA and the
accepted News schema remains metadata-only with no body column.

## 5. Control-path continuity

The pre-window handoff recorded `control_path_ok=1`. After monitoring attached,
the same read-only query succeeded twice against
`orderscope-state-live-canary`:

```text
first observed active check -> 1 (0.1377 ms)
active-window check         -> 1 (0.1712 ms)
post-rollback check         -> 1 (0.1527 ms)
```

All commands targeted D1 binding `STATE_DB`, database ID
`03c85865-1aa3-4b0c-b219-18987cd260a6`. No `7403`, abnormal control-query
stall, auth error, or control-path loss occurred.

## 6. Rollback verification

The checked-in baseline was deployed without CLI variable overrides using the
reviewed rollback message. Wrangler reported final version
`f6b35356-a7c2-40ed-8bbb-7b957f4ead11` and preserved the reviewed Cron and all
non-activation variables.

Independent post-deployment evidence showed:

```text
/health ok: true
/health mode: shadow
/health News mode: disabled
control_path_ok: 1
post-rollback scheduled timestamp: 2026-09-14T13:02:58.000Z
post-rollback News planned/selected/completed/failed: 0/0/0/0
post-rollback Worker outcome: ok
```

Repository HEAD remained the release commit and the working tree was clean
after the operational window.

## 7. Required return summary

```text
release commit: 56ee745ebf579ddb744d7113afce776192862473
pre-window Worker version: 16af6aeb-6818-4a09-be58-10aa7931a2de (deployment-history derived)
activation version: 2907cd45-7d7b-446e-99ca-b1f6b1a2d674
rollback/final version: f6b35356-a7c2-40ed-8bbb-7b957f4ead11
window start/end UTC: 2026-09-14 12:41:00.623 / 13:01:58.014
window start/end JST: 2026-09-14 21:41:00.623 / 22:01:58.014
eligible opportunities observed: 3 distinct
News jobs planned/completed/failed: 3 / 3 / 0
first eligible non-zero-seconds timestamp: 2026-09-14T12:50:58.000Z
normal external/tick: 2
max external/tick: 2 / 40
normal D1/tick: 9–15 eligible; 7 ineligible
max D1/tick: 21 / 40
control-path before/during/after: PASS / PASS / PASS
7403 observed: no
Market regression observed: no
CPU/resource failure observed: no
unauthorized symbols observed: no
News body persisted: no
secret leakage observed: no
final Worker mode: shadow
final News state: false
final Universe: canary-v0.1
final Cron: * * * * *
final disposition: ACCEPTED
reason: three eligible News opportunities completed within budget, control remained available, and safe rollback was independently verified
```
