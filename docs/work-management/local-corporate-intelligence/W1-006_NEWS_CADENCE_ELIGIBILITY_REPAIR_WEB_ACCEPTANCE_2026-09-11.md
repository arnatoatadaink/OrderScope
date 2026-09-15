# OrderScope — W1-006 News Cadence Eligibility Repair Web Acceptance

Status: **Accepted — local/non-live repair**
Date: 2026-09-11
Task: `W1-006 — Repair News cadence eligibility for Cron seconds offset`
Branch: `docs/mermaid-conventions-v0.1`

## 1. Decision

The News cadence eligibility repair is accepted for the local/non-live boundary.

The live Canary blocker recorded in `W1-001_LIVE_CANARY_CHANGE_WINDOW_REPORT_2026-09-11.md` was the exact-millisecond cadence predicate. A stable non-zero Cron seconds offset (observed as `:15`) prevented every nominal five-minute News opportunity from becoming eligible.

The repaired implementation evaluates cadence by UTC minute bucket instead of requiring the entire scheduled timestamp to be exactly divisible by the cadence duration. This preserves five-minute minute-boundary semantics while tolerating Cloudflare scheduler seconds offset.

## 2. Accepted behavior

For a five-minute cadence, the reviewed behavior is:

```text
14:00:00.000Z   -> eligible
14:00:15.000Z   -> eligible
14:00:59.999Z   -> eligible
14:01:15.000Z   -> not eligible
```

Session gating, checkpoint overlap behavior, News-disabled behavior, and After Hours planning remain intact.

## 3. Local verification returned by operator

```text
focused news-schedule tests: 7 passed / 7
full TypeScript tests:       128 passed / 128
focused duration:            202.019371 ms
full duration:               79650.843691 ms
git diff:                    clean
```

The `live-canary` dry-run/config surface remained safe:

```text
STATE_DB                         orderscope-state-live-canary
WORKER_MODE                      shadow
PREDICTION_MODE                  shadow
UNIVERSE_PROFILE                 canary-v0.1
ACQUISITION_MAX_JOBS_PER_TICK    2
NEWS_ACQUISITION_ENABLED         false
NEWS_ACQUISITION_CADENCE_MINUTES 5
NEWS_ACQUISITION_MAX_PAGES_PER_SYMBOL 2
NEWS_ACQUISITION_MAX_ARTICLES_PER_RUN 200
NEWS_ACQUISITION_CANARY_SYMBOLS  AMD,NVDA
```

No remote D1 mutation, Worker deployment, Cron change, Worker mode change, or News live activation was performed as part of this repair acceptance.

## 4. Scope of acceptance

This acceptance closes the cadence-code blocker only. It does not itself accept the Live Canary.

The earlier Canary remains `ROLLED_BACK`; its first authentication blocker was already repaired, and the cadence blocker is now locally repaired and verified. Runtime News correctness, provider paging distribution, production CPU, scheduler jitter, D1 rows/day, and provider-published-to-retrieved/accepted lag remain live evidence.

## 5. Critical-path transition

```text
W1-001 Stage B Accepted
  -> Live Canary #1 rolled back
  -> Alpaca 401 repaired
  -> cadence blocker identified
  -> W1-006 local repair Accepted (this document)
  -> review a new Live Canary change window
  -> explicit user approval
  -> redeploy reviewed build in safe shadow/News-disabled state
  -> reopen AMD/NVDA metadata-only Canary
  -> collect at least 12 eligible five-minute News opportunities unless a hard-stop condition fires
  -> runtime acceptance review
```

## 6. Reopen conditions

A new Live Canary window may be prepared because the code-level cadence blocker has been closed locally. Before activation, retain the existing safety sequence:

- identify the exact release SHA;
- verify `WORKER_MODE=shadow` and `NEWS_ACQUISITION_ENABLED=false` before deploy;
- verify the isolated `live-canary` D1 binding and that migration `0007_news_metadata.sql` is already applied/no unexpected migration is pending;
- verify required managed secret names without exposing values;
- deploy the reviewed build while still safe;
- observe at least one healthy shadow scheduled tick;
- only then open the explicitly approved live News Canary;
- retain combined external and D1 engineering ceilings of 40 each;
- disable News first on a News-only regression, then return Worker to shadow if broader safety requires it.

This document does not authorize the live operations above by itself.
