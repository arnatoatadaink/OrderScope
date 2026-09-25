# OrderScope — L1-003 PB-08 AMD/QQQ Gap Reproducibility Result

Status: **GAPS REPRODUCED / WINDOW NOT ACCEPTED DUE TO SECOND-CRON SPILLOVER**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## Local gate

PB-08 local acceptance passed before remote mutation:

```text
tests        30
pass         30
fail         0
typecheck    PASS
remoteMutation=false
```

## One-opportunity provider result

First live digest:

```text
2026-09-25T06:32:52.000Z
```

AMD:

```text
outcome      PARTIAL
inserted     0
matched      1
conflicts    0
rejected     0
missing      1
version      42
missing      2026-09-24T14:49:00Z -> 14:50:00Z
```

QQQ:

```text
outcome      PARTIAL
inserted     0
matched      1
conflicts    0
rejected     0
missing      1
version      11
missing      2026-09-24T14:32:00Z -> 14:33:00Z
```

Both symbols reproduced the exact same one-minute provider absence observed in
the first PB-08 attempt. No conflict, rejection or new missing timestamp was
introduced.

NVDA remained unchanged:

```text
v61 / 2026-09-23T18:28:00.000Z
COMPLETE
missing=[]
```

## Window defect

The verification script remained live while it queried post-opportunity
evidence. A second Cron tick began a SPY acquisition at:

```text
2026-09-25T06:33:52.000Z
job market-bars:0a5e77da63eef9eb
```

At the instant of the evidence query that SPY attempt was unresolved.

Therefore the AMD/QQQ reproducibility finding is valid, but the change-window
itself is not accepted as a strict one-opportunity window.

The script is fixed in:

```text
21b022d178180ff9278fe4b2226c118b2ed43a45
  Close PB-08 gap repro after one Cron opportunity
```

The corrected script restores the checked-in Shadow deployment immediately
after the first distinct live digest and restricts post-window attempt
classification to AMD/QQQ.

## Required reconciliation

Before any further live mutation, confirm read-only:

1. SPY attempt `market-bars:0a5e77da63eef9eb` final outcome;
2. SPY current checkpoint;
3. no unresolved canary acquisition attempts remain;
4. deployed Worker is Shadow;
5. NVDA remains v61 / COMPLETE.

## Interpretation

AMD 2026-09-24T14:49Z and QQQ 2026-09-24T14:32Z now have two independent
provider observations with the same missing identity and no conflicting bar.
They are candidates for explicit `REPRODUCIBLE_PROVIDER_ABSENCE` evidence.

The normal scheduler still cannot infer that evidence by itself. A separate,
explicit acknowledgement path is required before those gaps can stop taking
highest-priority MISSING_RANGE slots.

## Critical path

```text
PB-07  ACCEPTED
PB-08  LOCAL ACCEPTED
PB-08  first remote catch-up NOT ACCEPTED
PB-08  AMD/QQQ gaps REPRODUCED
PB-08  gap verification WINDOW NOT ACCEPTED
PB-08  SPY spillover reconciliation REQUIRED
PB-09  GATED
PB-10  NOT AUTHORIZED
```
