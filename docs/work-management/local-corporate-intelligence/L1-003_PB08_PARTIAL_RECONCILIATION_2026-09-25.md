# OrderScope — L1-003 PB-08 Partial Reconciliation

Status: **RECONCILED — NVDA entry intact; AMD/QQQ sparse IEX minutes block fairness**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## First PB-08 live opportunity

The authorized PB-08 frontier catch-up stopped on its first live scheduler
opportunity because both selected canary jobs were PARTIAL.

```text
digest 2026-09-25T04:42:23.000Z

AMD
  job     market-bars:878207aa69c72c23
  outcome PARTIAL
  pages   1
  inserted 99
  matched  0
  conflicts 0
  rejected  0
  missing   1

QQQ
  job     market-bars:73cd1e8d07f0526e
  outcome PARTIAL
  pages   1
  inserted 99
  matched  0
  conflicts 0
  rejected  0
  missing   1
```

The safe-close path restored the checked-in Shadow deployment.

## Remote checkpoint reconciliation

```text
AMD
  checkpoint        v41
  completeThrough   2026-09-24T14:49:00.000Z
  observedThrough   2026-09-24T15:10:00.000Z
  state             PARTIAL
  missing           2026-09-24T14:49:00Z -> 14:50:00Z
  retryNotBefore    2026-09-25T04:57:23.000Z

QQQ
  checkpoint        v10
  completeThrough   2026-09-24T14:32:00.000Z
  observedThrough   2026-09-24T15:10:00.000Z
  state             PARTIAL
  missing           2026-09-24T14:32:00Z -> 14:33:00Z
  retryNotBefore    2026-09-25T04:57:23.000Z

NVDA
  checkpoint        v61
  completeThrough   2026-09-23T18:28:00.000Z
  observedThrough   2026-09-23T18:28:00.000Z
  state             COMPLETE
  missing           []
  blocker           null
  retryNotBefore    null
```

The two PARTIAL jobs were AMD and QQQ. NVDA was not selected and the frozen
PB-08 NVDA entry itself was not mutated.

## Interpretation

The normal scheduler gives eligible `MISSING_RANGE` work highest priority.
AMD and QQQ therefore now occupy the two per-tick slots before NVDA forward
coverage can be selected.

The normal executor supports explicit `CoverageAbsenceEvidence`, but the
normal SchedulePolicy does not create or infer reproducible-provider-absence
evidence. Therefore repeatedly reopening the original PB-08 catch-up without
first resolving these two gaps can repeatedly block NVDA fairness.

One observation is not enough to classify either minute as
`REPRODUCIBLE_PROVIDER_ABSENCE`.

## Next bounded step

Use a separate one-opportunity gap reproducibility verification window.

Expected retry ranges, under the unchanged one-minute overlap:

```text
AMD
  2026-09-24T14:48:00Z -> 14:50:00Z
  target missing identity: 14:49:00Z

QQQ
  2026-09-24T14:31:00Z -> 14:33:00Z
  target missing identity: 14:32:00Z
```

Allowed outcomes for the verification window:

1. **REPAIRED**
   - provider returns the previously missing minute;
   - job succeeds cleanly;
   - missing range disappears.

2. **REPRODUCED**
   - job remains PARTIAL;
   - exactly the same one-minute missing identity remains;
   - no conflict/rejection/other missing timestamp appears.

Any other result is a stop condition.

This verification is separate from PB-08 NVDA catch-up and requires its own
explicit authorization because it performs remote provider acquisition and D1
checkpoint mutation for AMD/QQQ.

## Critical path

```text
PB-07  ACCEPTED
PB-08  LOCAL ACCEPTED
PB-08  first remote attempt NOT ACCEPTED
PB-08  reconciliation COMPLETE
PB-08  AMD/QQQ reproducibility verification NEXT
PB-09  GATED
PB-10  NOT AUTHORIZED
```
