# PX0-001 — Scheduler Registration Review

Status: **Provisional — local acceptance pending**
Date: 2026-09-12
Scope: reviewed operational scheduler registration only

## 1. Objective

PX0-001 does not add a new scheduler or authorize a live change. The current Worker already exposes a `scheduled()` handler and `wrangler.jsonc` already declares a once-per-minute Cron Trigger. This review freezes the intended registration boundary and detects configuration drift before a future reviewed change window.

## 2. Reviewed registration

The reviewed local registration is:

- Cron: `* * * * *` (UTC, once per minute)
- Worker entrypoint: existing Worker `scheduled()` handler
- `live-canary` Worker mode: `shadow`
- News acquisition: disabled
- Scheduler run evidence activation: disabled unless separately reviewed
- no Cron mutation, deployment, or remote D1 mutation in PX0-001 local acceptance

The once-per-minute trigger is intentionally separate from the five-minute News cadence. Scheduler opportunity logic decides whether a given tick is eligible; Cron registration must not encode News cadence as a second clock.

## 3. Drift guard

`src/scheduler-registration.ts` defines the reviewed registration contract.

`src/scheduler-registration.test.ts` verifies:

1. the reviewed Cron remains exactly one `* * * * *` entry;
2. `live-canary` remains `WORKER_MODE=shadow`;
3. `NEWS_ACQUISITION_ENABLED=false` remains true at registration review time;
4. scheduler run evidence is not silently activated;
5. the current `wrangler.jsonc` projection matches the reviewed registration.

A future change to Cron cadence, Worker live mode, News activation, or run-evidence activation must fail this review until deliberately updated and reviewed.

## 4. Closed-market / weekend work boundary

The U.S. equity market being closed does not block most remaining engineering work. During the closed-market window the following can be completed locally:

- PX0-001 registration contract and drift tests;
- full TypeScript/Python regression, typecheck, compileall, diff checks, and Wrangler dry-run;
- local scheduled-event simulation and duplicate/cadence fixtures;
- closed-session calendar fixtures proving no equity acquisition is invented when the market is closed;
- WBS/CP incorporation/remap for accepted PX0 and UWBS work;
- local D1-drain/export/purge fixture development while keeping real D1 mutation gated;
- backup/restore and replay failure fixtures;
- historical-data quality/replay tests using already captured data;
- operator/runbook and acceptance-checklist preparation.

The following require a future open-market or separately authorized remote window for final evidence:

- fresh U.S.-equity publication-to-retrieval / acceptance lag measurement;
- live session freshness/coverage observation at premarket/open/regular/after-hours boundaries;
- live Market + News shared-budget behavior under fresh incoming equity data;
- real D1 export/purge (`L1-003 / SMOKE-007` gate);
- migration `0008` remote application and scheduler-run-evidence activation;
- Worker/Cron mutation or another W1-001 confirmation/closeout Canary.

## 5. Weekend target state

A productive closed-market target is to finish all local/static acceptance work so that the next open-market window is evidence-only rather than implementation-heavy. At that point the remaining live work should be a short reviewed confirmation window, not feature development.

## 6. Local acceptance commands

```bash
npm test -- --test-name-pattern="scheduler registration"
npm run typecheck
npm run deploy:check
uv run pytest
python -m compileall analysis
git diff --check
```

For local Cron-trigger simulation, Cloudflare Wrangler supports `wrangler dev --test-scheduled`; this should remain local-only and must not be treated as live-market evidence.

## 7. Non-goals

PX0-001 does not authorize:

- changing the Cron expression;
- deploying a Worker;
- changing Worker mode to live;
- enabling News or scheduler evidence;
- changing D1 schema/data;
- opening a live Canary.
