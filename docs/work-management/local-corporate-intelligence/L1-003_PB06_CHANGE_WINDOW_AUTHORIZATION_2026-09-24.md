# OrderScope — L1-003 PB-06 Normal-Scheduler Handoff Change-Window Authorization

Status: **AUTHORIZED — execution pending operator invocation**
Date: 2026-09-24 JST
Environment: `live-canary`

## Authorized scope

This authorization covers only the bounded PB-06 normal-scheduler handoff window.

Frozen entry:

```text
coverage key          NVDA|1Min|REGULAR|stock:iex:raw
checkpoint            v58
complete through      2026-09-22T20:00:00.000Z
state                 COMPLETE
missing ranges        []
blocker               null
```

Expected accepted handoff:

```text
range                 2026-09-23T13:30:00.000Z -> 2026-09-23T15:10:00.000Z
expected bars         100
target checkpoint     v59
mode                  INCREMENTAL
due reason            FORWARD_COVERAGE
```

## Temporary runtime scope

The change window may temporarily switch only:

```text
WORKER_MODE shadow -> live
```

The following must remain unchanged:

- Cron: `* * * * *`
- Universe: `canary-v0.1`
- retention: 1,440 minutes
- maxJobsPerTick: 2
- maxBarsPerJob: 100
- priority policy
- IEX feed
- News disabled
- historical recovery disabled at baseline

## Maximum observation window

At most three distinct live scheduler opportunities are authorized.

The window must stop early as soon as NVDA is accepted at:

```text
v59 / 2026-09-23T15:10:00.000Z
```

If NVDA is not accepted within three opportunities, the window fails and must
restore the checked-in Shadow deployment.

## Mandatory acceptance evidence

Acceptance requires all of:

```text
final checkpoint ok     1
NVDA canonical bars     100
successful clean attempt >= 1
conflicts               0
rejected                0
missing                 0
state                   COMPLETE
missing ranges          []
blocker                 null
retry_not_before        null
```

Checkpoint movement must be explained by accepted normal-scheduler bars only.

## Mandatory safe close

On every exit path, the operator must:

```text
restore checked-in WORKER_MODE=shadow
keep News disabled
keep historical recovery disabled
remove temporary config
verify safe baseline
```

## Stop conditions

Stop and restore Shadow immediately if:

- moving retention floor has passed the Sep23 Regular open before activation;
- remote entry differs from the exact v58 state;
- an unresolved NVDA attempt exists;
- the deployed safe baseline is not Shadow / News disabled / historical closed;
- no distinct live scheduler opportunity is observed;
- NVDA does not reach exact v59 within three opportunities;
- final accepted-bar evidence differs from expectation;
- any configuration widening would be required.

## Operator command

Use only:

```bash
git pull --ff-only
bash scripts/l1_003_pb06_change_window.sh
```

## Out of scope

This authorization does not include:

- PB-07 stability observation;
- PB-08 or later Phase B preparation;
- Cron changes;
- Universe changes;
- priority changes;
- retention widening;
- News activation;
- historical recovery reactivation;
- manual checkpoint movement.
