# OrderScope — W1-004 Tiered Runtime Capacity Local Handoff

Status: **Ready for Local / non-live**
Date: 2026-09-11
Task: `W1-004 — Measure Tiered Runtime Capacity, Daily D1 Writes, and Backlog Age`
Depends on: `W1-003 — Bulk Coverage Checkpoint Reads and Shared D1 Budget Instrumentation` Accepted
Reference authority: `stock_monitoring_v0.1_universe_spec.md`

## 1. Purpose

W1-003 removed the 106-point checkpoint-read blocker and established shared D1 statement accounting. W1-004 must now measure whether the authoritative `full-v0.1` tiered Universe can operate within the reviewed D1/query/write constraints without allowing cadence backlog to grow without bound.

Authoritative Universe:

```text
Tier A / 1Min  = 25
Tier B / 15Min = 28
Tier C / 1Day  = 53
Total          = 106
```

Do not replace this with a 106-symbol 1-minute workload.

## 2. Scope

Local / fixture / dry-run only.

Measure or simulate one representative normal U.S. trading day using the real scheduling policy, tier cadences, overlap, finalization lag, `maxBarsPerJob`, job prioritization, and `maxJobsPerTick` configuration.

Keep separate evidence for:

- Tier A 1Min equities and BTCUSD 1Min crypto
- Tier B 15Min equities
- Tier C 1Day equities and ETHUSD 1Day crypto
- Market checkpoint bootstrap
- Market acquisition persistence
- attempts / lease / checkpoint CAS / stale-attempt summary
- News AMD/NVDA metadata job when enabled
- digest persistence

## 3. Required measurements

Report at minimum:

```text
normal-day planned bars 1Min
normal-day planned bars 15Min
normal-day planned bars 1Day
normal-day NEW bars
normal-day MATCHED/replayed observations
normal-day Market row writes
normal-day News row writes
normal-day other Worker row writes
normal-day total D1 row writes
shortened-day total D1 row writes
catch-up projection (separate from normal day)
normal combined external subrequests/tick
worst reviewed combined external subrequests/tick
normal combined D1 queries/tick
worst reviewed combined D1 queries/tick
max backlog age 1Min
max backlog age 15Min
max backlog age 1Day
end-of-day outstanding jobs by cadence
```

Rows written must be measured from actual local D1 mutation effects where practical; do not infer all writes from statement count. Separate NEW acceptance from overlap/MATCHED receipt traffic.

## 4. Backlog / cadence requirement

The existing priority policy orders MISSING_RANGE, then NO_CHECKPOINT, then oldest FORWARD_COVERAGE. It does not explicitly prioritize `1Min` over `15Min` or `1Day`.

Do not silently change this policy during measurement.

First measure the current behavior with the configured `ACQUISITION_MAX_JOBS_PER_TICK` value. If backlog grows without bound or Tier A freshness is materially worse than the 1-minute source cadence, stop and report the capacity blocker before changing scheduler semantics.

If a scheduler change is required, propose it as a separate reviewed task. Candidate changes may include cadence-aware priority, per-cadence quotas, or a reviewed increase in jobs per tick, but W1-004 itself does not authorize them.

## 5. Budget requirements

Preserve W1-003 instrumentation and fail-closed behavior.

Reviewed per-invocation engineering ceilings remain:

```text
external subrequests <= 40
D1 queries           <= 40
```

Prefer evidence materially below the ceilings rather than merely equal to them.

For daily D1 writes, report the measured/projected total and headroom against the current Free-plan daily row-write allowance used by the project. Do not change plan, database, retention, storage destination, or live settings in this task.

## 6. Catch-up separation

Do not mix historical catch-up with normal-day capacity.

Provide a separate catch-up projection covering at least one retention-window restart / empty-checkpoint scenario. If catch-up cannot fit within normal daily write headroom, report the required throttling or multi-day recovery requirement rather than weakening retention or idempotency semantics.

## 7. Required tests / evidence

Add focused fixtures that exercise a full 106-instrument tiered Universe across enough scheduled ticks to establish backlog behavior. Tests should cover at least:

1. normal full-v0.1 day
2. shortened U.S. session
3. empty checkpoints / catch-up
4. overlap / MATCHED replay accounting
5. News enabled AMD/NVDA combined tick
6. shared D1 budget enforcement
7. external retry accounting regression
8. deterministic scheduler results

Return:

```text
focused tests: pass/fail
full tests: pass/fail
typecheck: pass/fail
wrangler dry-run/build: pass/fail
git diff --check: pass/fail
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

## 8. Stop conditions

Stop and report Blocked if any of the following occurs:

- combined D1 queries exceed 40 in a reviewed tick
- combined external subrequests exceed 40 in a reviewed tick
- Tier A backlog grows without bound under current scheduler configuration
- daily write projection leaves no safe operating headroom
- normal operation depends on weakening receipt/idempotency/conflict/checkpoint semantics
- evidence requires remote D1, Worker deployment, Cron mutation, or Worker-mode change

## 9. Non-authorization

This handoff does **not** authorize:

- remote D1 migration or writes
- Worker deployment
- Cron changes
- Worker mode changes
- live Canary activation
- changing `full-v0.1` Universe membership
- changing Tier cadences
- increasing provider or Cloudflare plan limits

Return the measurement report for Web review before any live action.
