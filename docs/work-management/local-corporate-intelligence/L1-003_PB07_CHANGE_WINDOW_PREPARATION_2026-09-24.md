# OrderScope — L1-003 PB-07 Stability Change-Window Preparation

Status: **READY FOR LOCAL RE-ACCEPTANCE — remote activation not authorized**
Date: 2026-09-24 JST
Environment: `live-canary`

## Frozen entry

```text
coverage key          NVDA|1Min|REGULAR|stock:iex:raw
checkpoint            v59
complete through      2026-09-23T15:10:00.000Z
state                 COMPLETE
missing ranges        []
blocker               null
unresolved attempts   0
```

## Required stability evidence

PB-07 requires two consecutive selected NVDA normal-scheduler executions with
no intervening NVDA FAILED/PARTIAL/unresolved state.

```text
NVDA execution 1
  request  2026-09-23T15:09:00.000Z -> 2026-09-23T16:49:00.000Z
  target   v60 / 2026-09-23T16:49:00.000Z

NVDA execution 2
  request  2026-09-23T16:48:00.000Z -> 2026-09-23T18:28:00.000Z
  target   v61 / 2026-09-23T18:28:00.000Z
```

Each request contains 100 one-minute timestamps and a one-minute overlap with
already accepted coverage. A clean execution therefore requires
`inserted + matched = 100`, conflicts/rejected/missing all zero, and exact
checkpoint movement.

## Bounded live window

The reviewed fairness simulation requires at most seven Cron opportunities:

```text
1 AMD + QQQ
2 SPY + BTCUSD
3 BTCUSD + AMD
4 BTCUSD + NVDA  -> v60
5 QQQ + SPY
6 BTCUSD + AMD
7 NVDA + QQQ     -> v61
```

The operator script:

```bash
bash scripts/l1_003_pb07_change_window.sh
```

performs:
- activation-time retention recheck;
- full local acceptance rerun;
- Shadow / News-disabled / IEX / historical-closed baseline verification;
- exact v59 entry verification;
- temporary `WORKER_MODE=live` deployment only;
- observation of at most seven distinct live scheduler digests;
- per-tick `budget.withinBudget=true` verification;
- per-tick rejection of non-SUCCEEDED market summaries;
- separate observation of exact v60 before accepting v61;
- final exact v61 checkpoint validation;
- exactly two clean NVDA attempts in the window;
- zero bad/unresolved NVDA attempts;
- 199 canonical NVDA one-minute bars across the combined frozen interval;
- unconditional restoration of the checked-in Shadow deployment on exit.

## Unchanged runtime policy

- Cron remains `* * * * *`;
- Universe remains `canary-v0.1`;
- maxJobsPerTick remains 2;
- maxBarsPerJob remains 100;
- retention remains 1,440 minutes;
- fairness priority remains unchanged;
- feed remains IEX;
- News remains disabled;
- historical recovery remains disabled at baseline.

## Stop conditions

Stop and restore Shadow if:
- the moving retention floor passes the frozen first request start;
- exact v59 entry changes before activation;
- any live digest reports budget regression;
- any selected market job reports a non-SUCCEEDED result;
- any NVDA attempt is FAILED, PARTIAL or unresolved;
- v60 is not observed before v61;
- exact v61 is not reached within seven Cron opportunities;
- final canonical-bar or attempt evidence differs from the frozen expectation.

## Authorization boundary

This preparation authorizes no deploy, live-mode activation, provider call,
D1 mutation, PB-08 action, pause/resume action or Phase B.
