# OrderScope — W1-004 Tiered Runtime Capacity Blocker Report

Status: **Blocked — configured one-job scheduler materially misses Tier A cadence**
Date: 2026-09-11
Task: `W1-004 — Measure Tiered Runtime Capacity, Daily D1 Writes, and Backlog Age`
Input: `W1-004_TIERED_RUNTIME_CAPACITY_LOCAL_HANDOFF_2026-09-11.md`

## 1. Decision

The current `ACQUISITION_MAX_JOBS_PER_TICK=1` configuration does not provide
acceptable full-v0.1 Tier A freshness under the unchanged scheduler policy.
The deterministic normal-session fixture reaches a 69-minute 1Min backlog age
and still has nine 1Min jobs outstanding 30 minutes after the close. This is
materially worse than the one-minute source cadence and activates the explicit
W1-004 stop condition.

No cadence-aware priority, quota, or configuration increase was made. Such a
change requires a separate reviewed task.

## 2. Fixture boundary

The focused fixture uses the production `SchedulePolicy`,
`prioritizeAcquisitionJobs`, full-v0.1 Universe, one-minute Cron, configured
one-job selection, 24-hour retention, cadence overlap/finalization lag, and
`maxBarsPerJob=100`. It starts the session caught up so the measured delay is
queueing caused during the session, not inherited historical lag. A normal
390-minute session and a shortened 210-minute session are modeled through 30
minutes after close.

The full UTC-day planned bar counts are derived from the same authoritative
`24 equity + BTCUSD`, `28 equity`, and `52 equity + ETHUSD` route split.

## 3. Required measurements

```text
normal-day planned bars 1Min:                 10,800
normal-day planned bars 15Min:                   728
normal-day planned bars 1Day:                     53
normal-day NEW bars:                          11,581 projected target
normal-day MATCHED/replayed observations:      1,440 projected (one overlap/job)
normal-day Market row writes:                 37,623 projected
normal-day News row writes:                       78 projected empty-result fixture
normal-day other Worker row writes:           11,520 projected
normal-day total D1 row writes:               49,221 projected
Free daily write headroom (100,000):          50,779 projected

shortened-day planned NEW bars:                6,925
shortened-day total D1 row writes:            35,217 projected

normal combined external subrequests/tick:         1 (News-off), 3 (News tick)
worst reviewed combined external/tick:             9 (3 Market + 3 × 2 News attempts)
normal combined D1 queries/tick:                  19 (News-off), 22 empty News tick
worst reviewed combined D1 queries/tick:          28 (two one-article News pages)

max backlog age 1Min:                            69 minutes
max backlog age 15Min:                           68 minutes
max backlog age 1Day:                         1,470 minutes
end-of-day outstanding 1Min:                      9
end-of-day outstanding 15Min:                    15
end-of-day outstanding 1Day:                     51
```

`Market row writes` applies the locally measured persistence shapes retained
from W1-002: three rows per NEW bar and two rows per same-bar/new-receipt
MATCHED observation. Same-receipt replay remains zero. `other Worker` projects
five mutation rows per successful Market job (lease acquire/release, attempt
start/finish, checkpoint CAS) plus three digest mutation effects per minute.
News is deliberately separated and uses a conservative empty-result AMD/NVDA
job every five minutes during the regular session: one checkpoint row per job.
Article-dependent News writes are not safely projectable without an article
arrival distribution; the reviewed two-one-article-page query fixture remains
within the invocation ceiling.

The row totals describe the cost of achieving complete target coverage. The
current scheduler did **not** achieve those target NEW counts by end of day, so
the headroom figure is not an acceptance result.

## 4. Scheduler evidence

```text
normal selected jobs through close+30m:
  1Min 182 / 15Min 236 / 1Day 1

shortened selected jobs through close+30m:
  1Min 107 / 15Min 131 / 1Day 1

normal outstanding through close+30m:
  1Min 9 / 15Min 15 / 1Day 51

shortened outstanding through close+30m:
  1Min 9 / 15Min 15 / 1Day 51
```

The large 1Day age includes the intentional wait from the previous session
close until the current daily bar finalizes. The blocker is independent of that
daily behavior: Tier A alone is 69 times its source cadence.

## 5. Catch-up separation

An empty-checkpoint retention-window fixture produces all 106 deterministic
`NO_CHECKPOINT` jobs. With one selected job per tick, bootstrap selection alone
takes at least 106 minutes; 1Min ranges additionally require multiple bounded
100-bar jobs. The target retention window contains the same 11,581 NEW bars as
the normal-day model before overlap and operational rows.

The projected persistence volume can fit under 100,000 rows in isolation, but
catch-up cannot be mixed into normal operation while preserving Tier A
freshness at the current selection rate. Recovery therefore requires a reviewed
throttle/multi-day policy or increased/cadence-aware capacity; neither is
authorized by W1-004.

## 6. Verification

```text
focused tests: pass
full tests: pass
typecheck: pass
wrangler dry-run/build: pass
git diff --check: pass
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

Covered evidence includes normal full-v0.1, shortened session, empty checkpoint
catch-up, overlap/MATCHED persistence, AMD/NVDA News combined invocation,
shared D1 budget enforcement, external retry accounting, and deterministic
scheduler output.

## 7. Required follow-up

Open a separate reviewed scheduler-capacity task. Candidate designs are
cadence-aware priority, per-cadence quotas, or a reviewed increase to
`ACQUISITION_MAX_JOBS_PER_TICK`. Re-run W1-004 after one option is authorized;
do not activate full-v0.1 or News live from this result.
