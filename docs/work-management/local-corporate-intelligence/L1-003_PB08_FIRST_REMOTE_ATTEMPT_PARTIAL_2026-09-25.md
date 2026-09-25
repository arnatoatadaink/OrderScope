# OrderScope — L1-003 PB-08 First Remote Attempt

Status: **NOT ACCEPTED — stopped safely after PARTIAL scheduler outcomes**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## Result

The first authorized PB-08 frontier catch-up execution passed local acceptance
and the exact remote-entry gate, deployed the temporary live configuration,
then stopped on the first observed scheduler opportunity.

Observed first live digest:

```text
generated_at  2026-09-25T04:42:23.000Z

job 1
  outcome     PARTIAL
  pages       1
  inserted    99
  matched     0
  conflicts   0
  rejected    0
  missing     1

job 2
  outcome     PARTIAL
  pages       1
  inserted    99
  matched     0
  conflicts   0
  rejected    0
  missing     1
```

The change-window script correctly treated any non-SUCCEEDED market summary as
a stop condition and aborted before accepting PB-08.

## Safety result

The EXIT safe-close path restored the checked-in Shadow deployment.

Observed restored baseline:

```text
WORKER_MODE              shadow
PREDICTION_MODE          shadow
ALPACA_FEED              iex
UNIVERSE_PROFILE         canary-v0.1
NEWS_ACQUISITION_ENABLED false
HISTORICAL_RECOVERY_ENABLED false
Cron                     * * * * *
```

PB-08 frontier catch-up is therefore **not accepted**.

## Required reconciliation

Do not rerun the live catch-up yet.

First establish, read-only:

1. which two coverage keys correspond to the two PARTIAL jobs;
2. exact requested ranges for those jobs;
3. exact missing timestamps;
4. resulting checkpoint versions and COMPLETE/PARTIAL states;
5. whether NVDA itself was selected or remained at the frozen v61 entry;
6. whether the PARTIAL results represent reproducible provider absence,
   ordinary retained-history sparsity, or a planner/executor defect;
7. whether the frozen PB-08 entry packet is still valid after the mutation.

Only after that reconciliation may PB-08 be re-frozen or repaired.

## Critical path

```text
PB-07  ACCEPTED
PB-08  LOCAL ACCEPTED
PB-08  FIRST REMOTE ATTEMPT: NOT ACCEPTED / PARTIAL
PB-08  RECONCILIATION REQUIRED
PB-09  GATED
PB-10  NOT AUTHORIZED
```

No PB-09 / PB-10 / Phase B pause-resume authorization is implied.
