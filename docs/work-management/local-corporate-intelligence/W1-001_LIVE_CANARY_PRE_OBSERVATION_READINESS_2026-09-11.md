# OrderScope — W1-001 Live Canary Pre-Observation Readiness

Status: **Ready to activate only inside a supervised U.S. observation window**
Date: 2026-09-11
Task: `W1-001 — AMD/NVDA metadata-only News Live Canary reopen`
Release: `5ab43cfc2a7d074f4ca6c1ee01c723cfb0a7d06b`
Safe deploy version: `c287a96d-ab5c-465f-82b1-41658d18c258`

## 1. Current verified state

Pre-observation work is complete through safe deployment. The remote state must remain unchanged until an actively supervised U.S. observation window begins.

Recorded evidence:

```text
focused news-schedule tests: 7 / 7 passed
full TypeScript suite:      128 / 128 passed
typecheck:                  passed
cf-typegen:                 passed
Wrangler live-canary dry-run/build: passed
Alpaca calendar/auth:       HTTP 200
pending D1 migrations:      none
shadow scheduled tick:      outcome ok
shadow CPU:                 0 ms observed
working tree:               clean
upstream:                   synchronized
```

Current remote safety state:

```text
WORKER_MODE=shadow
NEWS_ACQUISITION_ENABLED=false
UNIVERSE_PROFILE=canary-v0.1
NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
NEWS_ACQUISITION_CADENCE_MINUTES=5
Cron=* * * * *
```

Do not activate while the operator cannot supervise immediate rollback.

## 2. Observation-window start gate

Before activation, confirm all of the following in one short preflight:

- release SHA remains the reviewed release or a separately reviewed descendant;
- deployed safe version is known;
- Worker is still `shadow`;
- News is still disabled;
- Universe is still `canary-v0.1`;
- Cron is still one minute;
- no new D1 migration is pending;
- Alpaca calendar/auth remains healthy;
- no unrelated runtime variable changed;
- operator can remain present for first eligible News buckets and immediate rollback.

If any item differs, stop and reconcile before activation.

## 3. First-hour evidence worksheet

Capture one row for each eligible five-minute News opportunity. Do not capture News bodies, secret values, or auth headers.

| # | scheduledAt | runStartedAt | News planned/completed/failed | pages | raw obs | ext Market/News/total | D1 Market/News/total | withinBudget | CPU/resource | notes |
|---|---|---|---|---:|---:|---|---|---|---|---|
| 1 | | | | | | | | | | |
| 2 | | | | | | | | | | |
| 3 | | | | | | | | | | |
| 4 | | | | | | | | | | |
| 5 | | | | | | | | | | |
| 6 | | | | | | | | | | |
| 7 | | | | | | | | | | |
| 8 | | | | | | | | | | |
| 9 | | | | | | | | | | |
| 10 | | | | | | | | | | |
| 11 | | | | | | | | | | |
| 12 | | | | | | | | | | |

For article-bearing runs, additionally record aggregate publication-to-retrieval and publication-to-acceptance lag summaries where available.

## 4. Immediate cadence proof

The first technical objective after activation is to prove the W1-006 repair in production.

Expected eligible timestamps include scheduler starts such as:

```text
HH:00:15Z
HH:05:15Z
HH:10:15Z
...
```

The exact seconds offset may vary; eligibility is based on the UTC minute bucket.

Acceptance for this repair in live execution:

- a non-zero-seconds five-minute bucket produces a News plan when the session and checkpoint allow it;
- adjacent non-cadence minutes do not produce News plans;
- no Cron change is required.

If News remains enabled but repeatedly plans zero jobs across expected eligible buckets, stop and roll back without changing Cron.

## 5. Hard-stop card

Immediately begin rollback if any of the following occurs:

```text
combined external subrequests > 40 or fail-before-crossing breaks
combined D1 queries > 40 or fail-before-crossing breaks
Market path regresses after News activation
repeated Worker CPU/exceeded-resource failures
unauthorized symbol expansion beyond AMD/NVDA
false checkpoint advancement after partial/retryable failure
News body / secret / auth-header leakage
unexpected D1/schema corruption
cadence repair still fails live
continuation requires an unreviewed code/config delta
```

Preferred rollback sequence:

1. `NEWS_ACQUISITION_ENABLED=false`;
2. verify zero News provider calls/mutations on a subsequent invocation;
3. if needed, restore `WORKER_MODE=shadow`;
4. if release regression remains, restore the last known-good Worker version;
5. leave additive migration `0007_news_metadata.sql` in place.

## 6. Decision after 12 eligible opportunities

Choose exactly one:

- `ACCEPTED`: applicable live criteria satisfied;
- `INCONCLUSIVE`: no hard failure but insufficient live evidence, e.g. no article arrivals;
- `ROLLED_BACK`: hard-stop condition fired and safe rollback completed;
- `BLOCKED`: a new reviewed technical/configuration delta is required.

Do not expand to `full-v0.1`, alter Cron, cadence, page limits, symbol scope, or budget ceilings during this window.

## 7. Post-window report minimum

Record:

```text
release commit
pre-window version
safe deploy version
activation version
rollback version if any
window start/end UTC/JST
final Worker mode
final News enabled state
final Universe profile
final Cron
eligible News opportunities observed
News jobs planned/completed/failed
first non-zero-seconds eligible timestamp
normal/max external per tick
normal/max D1 per tick
Market regression yes/no
CPU/resource failure yes/no
News bodies persisted no
secret leakage observed no
runtime News lag summary
scheduler jitter summary
D1 write-volume evidence
final disposition and reason
```

Then update the integrated progress tracker with the final disposition and next critical-path gate.
