# OrderScope — L1-003 PB-07 Opportunity Semantics

Status: **PREPARATION CLARIFIED — remote activation not authorized**
Date: 2026-09-24 JST

## Why this clarification is required

PB-07 acceptance says that at least two consecutive eligible scheduler
opportunities must advance the same coverage cleanly.

The unchanged canary scheduler has:

```text
maxJobsPerTick = 2
fairness        = oldest forward coverage first
Universe        = AMD, QQQ, SPY, NVDA, BTCUSD
```

At the PB-07 read-only snapshot, NVDA is healthy and current at v59, while the
other canary checkpoints remain older. Therefore NVDA is eligible for planning
on every Cron tick, but fairness does not select it on every Cron tick.

Literal "two consecutive Cron ticks" would require changing fairness,
maxJobsPerTick, or Universe to force NVDA selection. That would violate the
unchanged-normal-scheduler requirement.

## Operational interpretation

For PB-07, "two consecutive eligible scheduler opportunities for the same
coverage" means two consecutive **selected NVDA normal-scheduler executions**
with no intervening NVDA failure, partial result, conflict, rejected record,
missing range, blocker, or manual checkpoint movement.

Other Cron ticks that legitimately select older canary work under unchanged
fairness do not break NVDA stability because they are not NVDA execution
opportunities.

The entire live observation window is still bounded, and any unexpected
scheduler failure or unsafe state is a stop condition.

## Frozen fairness-order expectation

Using the read-only checkpoint snapshot and unchanged priority policy, the local
simulation freezes this six-opportunity upper bound:

```text
Cron opportunity 1  AMD + QQQ
Cron opportunity 2  SPY + BTCUSD
Cron opportunity 3  AMD + NVDA   -> NVDA v60 / 16:49Z
Cron opportunity 4  QQQ + SPY
Cron opportunity 5  BTCUSD + AMD
Cron opportunity 6  BTCUSD + NVDA -> NVDA v61 / 18:28Z
```

Thus the bounded remote window may require up to six Cron opportunities to
observe two consecutive selected NVDA executions.

The expected NVDA executions are:

```text
selected NVDA execution 1
  before   v59 / 2026-09-23T15:10:00.000Z
  request  2026-09-23T15:09:00.000Z -> 2026-09-23T16:49:00.000Z
  after    v60 / 2026-09-23T16:49:00.000Z

selected NVDA execution 2
  before   v60 / 2026-09-23T16:49:00.000Z
  request  2026-09-23T16:48:00.000Z -> 2026-09-23T18:28:00.000Z
  after    v61 / 2026-09-23T18:28:00.000Z
```

## Acceptance conditions

Both selected NVDA executions must be:
- normal scheduler jobs;
- `SUCCEEDED`;
- conflict = 0;
- rejected = 0;
- missing = 0;
- checkpoint state `COMPLETE`;
- no missing ranges;
- no blocker;
- no retry_not_before;
- exact expected checkpoint version and boundary.

There must be no intervening NVDA attempt with FAILED or PARTIAL outcome.

## Authorization boundary

This clarification changes no runtime configuration and authorizes no deploy,
provider call, D1 mutation, live-mode activation, PB-08 action, or Phase B.
