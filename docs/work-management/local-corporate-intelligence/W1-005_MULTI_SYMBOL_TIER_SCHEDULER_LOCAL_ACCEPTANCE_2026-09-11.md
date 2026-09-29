# OrderScope — W1-005 Multi-Symbol Tier Scheduler Local Acceptance

Status: **Accepted for local/non-live implementation**
Date: 2026-09-11

## Result

The production planner now collapses compatible single-instrument plans into bounded provider batches after priority ordering. Provider route, cadence, session scope, logical variant, acquisition mode, requested half-open range, calendar revision, and Universe revision must match. Instruments and checkpoint expectations remain positionally aligned and deterministic.

Alpaca stock and crypto adapters issue one symbols-list request per batch and retain page tokens across symbol-first responses. Execution attributes normalized observations, missing coverage, and checkpoint progression independently per symbol. A page that omits a requested symbol cannot prove that symbol complete. Checkpoint completion uses one set-oriented D1 CAS statement with per-symbol expected-version predicates.

The checked-in local/shadow configuration selects at most two batch groups per tick. This is enough for the deterministic full-v0.1 fixture while retaining headroom under the reviewed combined ceilings; it is not a live activation authorization.

## Capacity evidence

```text
W1-005 status: Accepted (local/non-live)
authoritative Universe: 25 / 28 / 53 = 106
steady groups: stock 1Min=24, crypto 1Min=1, stock 15Min=28, stock 1Day=52, crypto 1Day=1
selected groups/tick: max 2
normal selected groups: 783 1Min / 26 15Min / 1 1Day
shortened selected groups: 435 1Min / 14 15Min / 1 1Day
normal max backlog age 1Min: 3 minutes
normal max backlog age 15Min: 17 minutes
shortened max backlog age 1Min: 3 minutes
shortened max backlog age 15Min: 17 minutes
outstanding 1Min at close+30m: 0 (normal and shortened)
outstanding 15Min at close+30m: 0 (normal and shortened)
outstanding 1Day at reviewed deadline: 0 (normal and shortened)
normal-day NEW bars: 11,581
shortened-day NEW bars: 6,925
normal/worst Market external requests per tick: <=2 before provider retries/pages
reviewed combined external ceiling: 40, fail-before-crossing retained
reviewed combined D1 ceiling: 40, fail-before-crossing retained
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

The daily age reported by the simulator begins at the preceding session checkpoint (1,470 minutes normal; 1,290 shortened); the due daily group completes on the first eligible tick at close plus the configured 30-minute finalization lag, so same-day completion delay after eligibility is zero minutes.

## Verification

- focused scheduler/capacity/orchestration: 33 passed
- full TypeScript suite: 124 passed
- TypeScript typecheck: passed
- Wrangler type generation: passed
- Wrangler deploy dry-run/build: passed; no deployment performed
- `git diff --check`: passed

Cloudflare guidance was rechecked before the Worker changes. Request state remains invocation-local, promises remain awaited or attached to `ctx.waitUntil()`, D1 continues through bindings, and no secret or response body persistence was introduced.

## Boundary

This acceptance is local fixture evidence only. It does not authorize remote D1 mutation, deployment, Cron changes, `WORKER_MODE` changes, full-v0.1 live acquisition, or News live activation. Live CPU, provider paging distribution, and scheduler delay remain Canary measurements.
