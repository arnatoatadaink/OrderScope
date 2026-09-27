# OrderScope — L1-003 PB-06 Normal-Scheduler Change-Window Preparation

Status: **READY FOR LOCAL RE-ACCEPTANCE — remote scheduler activation not authorized**
Date: 2026-09-24 JST
Environment: `live-canary`

## Scope

PB-06 proves handoff from accepted historical coverage into the unchanged
normal scheduler.

Frozen entry:

```text
NVDA coverage key   NVDA|1Min|REGULAR|stock:iex:raw
version             58
complete through    2026-09-22T20:00:00.000Z
state               COMPLETE
missing ranges      []
blocker             null
```

Expected accepted handoff:

```text
first NVDA range    2026-09-23T13:30:00.000Z -> 2026-09-23T15:10:00.000Z
expected bars       100
expected version    59
mode                INCREMENTAL
due reason          FORWARD_COVERAGE
```

## Safety fix inherited

The normal scheduler executes prioritized single-instrument jobs for PB-06.
This avoids the latent aggregate batch bar-limit mismatch and preserves
fairness order.

Unchanged:
- max jobs/tick = 2;
- max bars/job = 100;
- retention = 1,440 minutes;
- Universe = canary-v0.1;
- Cron = every minute;
- IEX feed;
- News disabled;
- historical recovery disabled at baseline.

## Bounded live window

The operator script is:

```bash
bash scripts/l1_003_pb06_change_window.sh
```

The script:
1. rechecks the moving retention floor;
2. reruns PB-06 local tests/typecheck;
3. verifies Shadow/News-disabled/historical-closed baseline;
4. asserts exact remote entry v58;
5. generates a temporary config changing only `WORKER_MODE` from Shadow to Live;
6. deploys the temporary live config without changing Cron;
7. observes at most three distinct live scheduler opportunities;
8. stops early when NVDA reaches exactly v59 / Sep23 15:10Z;
9. verifies 100 canonical NVDA bars and at least one clean successful attempt;
10. always restores the checked-in Shadow deployment on exit.

No scheduler evidence flag, Universe change, retention widening, priority change,
Cron change, News activation or historical recovery route is introduced.

## Stop conditions

Fail and restore Shadow if any of these occurs:
- retention floor has passed Sep23 Regular open before activation;
- entry checkpoint differs from v58 / Sep22 close;
- unresolved NVDA attempt exists;
- deployed safe baseline is not Shadow / News disabled / historical endpoint 404;
- no distinct live Cron opportunity is observed;
- NVDA does not reach the exact expected v59 checkpoint within three opportunities;
- final canonical-bar or clean-attempt evidence differs from expectation.

## Authorization boundary

No remote deployment or scheduler activation is authorized by this preparation.
After local re-acceptance, a separate PB-06 change-window authorization is required.
