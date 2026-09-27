# OrderScope — W1-001 Live Canary Reopen Change-Window Report

Status: **ROLLED_BACK — required Canary evidence collected; monitoring control was lost during closeout**
Date: 2026-09-11 JST
Task: `W1-001 — Worker/Schedule News metadata acquisition Live Canary reopen`
Release commit: `5ab43cfc2a7d074f4ca6c1ee01c723cfb0a7d06b`
Branch: `docs/mermaid-conventions-v0.1`
Environment: `live-canary`
Handoff: `W1-001_LIVE_CANARY_REOPEN_LOCAL_HANDOFF_2026-09-11.md`

## 1. Final disposition

The reviewed AMD/NVDA metadata-only reopen produced the required 12 distinct
five-minute News opportunities and demonstrated that the W1-006 minute-bucket
repair works with a non-zero Cron seconds offset. All 12 reviewed opportunities
completed without a News partial/failure or budget crossing.

The final disposition is nevertheless `ROLLED_BACK`. During closeout, a
read-only Cloudflare D1 evidence request stalled and ultimately returned API
error `7403` (account invalid or not authorized). Because continued live
operation could no longer be monitored reliably, the activation pair was
returned to the safe state. The final remote state is:

```text
Worker version: 16af6aeb-6818-4a09-be58-10aa7931a2de
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
NEWS_ACQUISITION_CADENCE_MINUTES=5
Cron=* * * * *
```

This disposition does not invalidate the cadence-repair evidence, but it does
not authorize leaving the Canary enabled or activating `full-v0.1`.

## 2. Release and pre-window evidence

```text
focused News schedule tests -> 7 passed
full TypeScript suite       -> 128 passed
TypeScript typecheck        -> passed
Cloudflare type generation  -> passed
Wrangler live-canary dry-run -> passed
git diff --check            -> passed
working tree before window  -> clean
Alpaca calendar auth check  -> HTTP 200
pending D1 migrations       -> none
```

Remote preflight confirmed the isolated
`orderscope-state-live-canary` D1 binding, both required managed secret names,
the one-minute Cron, `canary-v0.1`, AMD/NVDA only, and the safe activation
baseline. No secret values or authentication headers were recorded.

## 3. Deployment timeline

All timestamps are UTC. Add nine hours for JST.

| Time | Version | Event | Result |
|---|---|---|---|
| 2026-09-11 02:49:52 | `c287a96d-ab5c-465f-82b1-41658d18c258` | W1-006 release deployed with `shadow` / News disabled | Healthy shadow tick at `02:51:15Z` |
| 2026-09-11 08:03:16 | `0b3d744b-e0db-4d6d-817a-167de0d516d8` | AMD/NVDA News activation | Activated only the reviewed pair |
| 2026-09-11 08:05:30 | same | First distinct eligible bucket | News `planned/selected/completed=1/1/1` |
| 2026-09-11 09:00:30 | same | Twelfth distinct eligible bucket | News completed; duplicate identity matched |
| before 2026-09-11 13:03:13 | `16af6aeb-6818-4a09-be58-10aa7931a2de` | Monitoring-control rollback | Healthy `shadow`; News disabled |

The reviewed evidence window was `08:03:16–09:01:30Z`
(`17:03:16–18:01:30 JST`). The activation remained deployed after the evidence
window while closeout API calls stalled. When the API returned authorization
error `7403`, rollback was performed immediately on regaining control.

## 4. Cadence and runtime evidence

Distinct eligible buckets reviewed:

```text
08:05:30  08:10:30  08:15:30  08:20:30
08:25:30  08:30:30  08:35:30  08:40:30
08:45:30  08:50:30  08:55:30  09:00:30 UTC
```

An additional deployment-transition invocation at `08:05:46Z` was observed
but was not counted as a distinct five-minute opportunity. Ineligible minutes
consistently planned zero News jobs. No Cron change was needed.

For the 12 distinct reviewed opportunities, plus the separately identified
deployment-transition invocation:

```text
News jobs planned/completed/failed -> 13 / 13 / 0
News partial jobs                  -> 0
News pages                         -> 26
article observations/duplicates   -> 2 / 1
normal external/tick              -> 2
max external/tick                 -> 2 / 40
normal D1/tick                     -> 9
max D1/tick                        -> 21 / 40 (Market gap-retry tick)
article-bearing News D1/tick       -> 12 / 40
withinBudget                       -> true for every reviewed tick
```

Market scheduled work remained within budget. Premarket missing-range retries
returned `PARTIAL` with the unresolved missing item retained; no false coverage
advance, Market `FAILED` outcome, conflict, or rejection was observed. Wrangler
tail reported each reviewed invocation as `Ok`; no exceeded-resource, CPU,
exception, 429, or 5xx indicator appeared. The retained digest exposes the
scheduled timestamp but not separate run-start/run-finish timestamps, so a
numeric scheduler-delay or run-duration distribution was not available. The
stable observed scheduler offset was `:30` seconds.

## 5. News correctness and lag

During the reviewed evidence window, D1 contained one newly accepted article
identity and one `NVDA` query membership. It was observed again at `09:00:30Z`
as a duplicate without creating a second canonical row. No unauthorized query
symbol was present.

```text
provider published_at -> first_retrieved_at -> 351 seconds
provider published_at -> accepted_at        -> 951 seconds
canonical article rows created in window    -> 1
query memberships created in window         -> 1 (NVDA)
```

The `news_article` schema contains provider identity, headline/publisher/URL,
provider timestamps, symbol metadata, content identity, retrieval timestamps,
and acceptance time. It has no News body column. No News body, credential, or
authentication-header leakage was observed.

The window did not encounter 429, 5xx, page-cap, or token-loop behavior; their
accepted retryable/fail-closed behavior remains supported by the local suite,
but was not re-exercised live.

## 6. D1 write-volume evidence

Empty-result eligible News runs used two provider pages and three News D1
queries. The article-bearing run used six News D1 queries and produced one
canonical article row plus one query-membership row. Re-observation produced a
duplicate count rather than another canonical article. This supports a
metadata-row/write projection driven by new provider identities and symbol
memberships, rather than raw observations or response-body size.

## 7. Rollback verification

Rollback version `16af6aeb-6818-4a09-be58-10aa7931a2de` was deployed with the
checked-in safe baseline. `/health` returned `ok=true`, `mode=shadow`, and News
disabled. The subsequent `13:03:30Z` scheduled shadow invocation was `Ok` with
News `planned/selected/completed/failed=0/0/0/0`; therefore post-rollback News
provider calls and News acquisition mutations were zero.

## 8. Required return summary

```text
release commit: 5ab43cfc2a7d074f4ca6c1ee01c723cfb0a7d06b
pre-window Worker version: c2aebaa7-d82a-4f79-986a-5700b01a5146
safe deploy version: c287a96d-ab5c-465f-82b1-41658d18c258
activation version: 0b3d744b-e0db-4d6d-817a-167de0d516d8
rollback version: 16af6aeb-6818-4a09-be58-10aa7931a2de
window start/end UTC: 2026-09-11 08:03:16 / 09:01:30
window start/end JST: 2026-09-11 17:03:16 / 18:01:30
final Worker mode: shadow
final News enabled state: false
final Universe profile: canary-v0.1
final Cron: * * * * *
eligible News opportunities observed: 12 distinct
News jobs planned/completed/failed: 13 / 13 / 0 (12 distinct buckets plus one deployment-transition invocation)
first non-zero-seconds eligible timestamp: 2026-09-11T08:05:30Z
normal external/tick: 2
max external/tick: 2
normal D1/tick: 9
max D1/tick: 21
Market regression observed: no
CPU/resource failure observed: no
News bodies persisted: no
secret leakage observed: no
runtime News lag summary: retrieval 351 s; acceptance 951 s (one window article)
scheduler jitter summary: stable :30 seconds offset; separate delay unavailable
D1 rows/write projection evidence: one canonical row and one membership for one new identity; duplicate re-observation added no canonical row
final disposition: ROLLED_BACK
reason: Cloudflare API authorization loss prevented reliable closeout monitoring; safe rollback completed
```
