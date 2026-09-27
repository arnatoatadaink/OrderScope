# OrderScope — L1-003 PB-08 Reproducible Provider Absence Acknowledgement Authorization

Status: **AUTHORIZED FOR ONE BOUNDED CHANGE WINDOW**
Date: 2026-09-25 JST
Branch: `l1-003-local-market-recovery`

## Local acceptance

```text
tests        33
pass         33
fail         0
typecheck    PASS
PB-08 local acceptance PASS
remoteMutation=false
```

The accepted test set includes:
- frozen AMD/QQQ reproduced-gap recognition;
- acknowledgement progression through only the reproduced absent minute;
- rejection of checkpoint drift and non-canonical acknowledgement timestamps.

## Authorized remote mutation

Authorize one execution of:

```text
scripts/l1_003_pb08_absence_ack_change_window.sh
```

Frozen acknowledgement targets:

```text
AMD
  entry  v42 / PARTIAL
  absent 2026-09-24T14:49:00.000Z
  exit   v43 / COMPLETE / 2026-09-24T14:50:00.000Z

QQQ
  entry  v11 / PARTIAL
  absent 2026-09-24T14:32:00.000Z
  exit   v12 / COMPLETE / 2026-09-24T14:33:00.000Z

NVDA
  must remain v61 / COMPLETE / 2026-09-23T18:28:00.000Z
```

The acknowledgement reason is:

```text
REPRODUCIBLE_PROVIDER_ABSENCE
observations=2
```

## Safety envelope

The change window must:
- require the exact frozen AMD/QQQ/NVDA checkpoint identities;
- require zero unresolved canary attempts;
- require Shadow / News-disabled / IEX;
- require the acknowledgement endpoint to be 404 before gate opening;
- open the gate only temporarily;
- use a temporary control token;
- perform the acknowledgement once;
- require both AMD and QQQ rows to update together;
- verify AMD v43 / QQQ v12 COMPLETE and missing=[] afterward;
- verify NVDA remains unchanged;
- restore gate=false Shadow;
- delete the temporary control token;
- confirm the endpoint returns 404 after close.

Any mismatch is a stop condition.

## Authority boundary

This authorization does not include:
- PB-09;
- PB-10;
- Phase B pause/resume;
- NVDA frontier catch-up execution;
- retention widening;
- Universe changes;
- priority changes;
- Cron changes;
- historical recovery.
