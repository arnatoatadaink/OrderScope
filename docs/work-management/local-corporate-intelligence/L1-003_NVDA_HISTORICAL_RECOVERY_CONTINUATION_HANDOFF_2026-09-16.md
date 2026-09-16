# OrderScope — L1-003 NVDA Historical Recovery Continuation Handoff

Status: **LOCAL IMPLEMENTATION ACCEPTED — continuation deploy and remote execution not authorized**
Date: 2026-09-16 JST
Parent: `L1-003_NVDA_HISTORICAL_RECOVERY_CHANGE_WINDOW_2026-09-16.md`

## 1. Purpose and boundary

Continue the accepted NVDA historical recovery after checkpoint version 7
without creating a broadly mutable backfill endpoint. Each invocation may run
only the next deterministic chunk derived from the current persisted checkpoint
and the unchanged frozen recovery/calendar identity.

This handoff does not authorize deployment, secret creation, gate activation,
provider execution, D1 writes, a second chunk, normal-scheduler activation, or
Phase B.

## 2. Continuation contract

The new endpoint is:

```text
POST /control/historical-recovery/nvda/next-chunk
```

It remains protected by the existing default-false
`HISTORICAL_RECOVERY_ENABLED` gate and the separately provisioned
`HISTORICAL_RECOVERY_CONTROL_TOKEN` Bearer secret. It accepts no request body.
Every request must provide:

```text
x-orderscope-recovery-id
x-orderscope-job-id
x-orderscope-checkpoint-version
x-orderscope-complete-through
```

The handler fails before provider work unless all of these conditions hold:

- Worker mode is Shadow and News is disabled;
- feed is `iex` and Universe profile is `canary-v0.1`;
- recovery, provider, Universe, calendar, instrument, session, variant, start,
  end, page and bar bounds remain frozen;
- supplied checkpoint version is an integer at least 7;
- supplied complete-through is canonical UTC;
- the persisted checkpoint is COMPLETE, has no missing ranges, and exactly
  matches the supplied version and boundary;
- the authoritative calendar retains revision
  `alpaca-calendar-v2:da7d32f3`;
- replanning from persisted truth and the verified authoritative calendar
  produces exactly the supplied job ID before any bar-provider call or D1
  mutation.

After these checks, the handler acquires the existing D1 lease, invokes the
normal acquisition executor once, verifies the exact expected bar count and
version increment, releases the lease, and stops. A replay of the same headers
fails checkpoint preflight before another provider call. No loop or automatic
next-chunk invocation exists.

## 3. Version-7 next candidate

The locally reviewed next deterministic chunk is:

```text
recovery_id                  L1-003-NVDA-20260916-01
checkpoint_version           7
checkpoint_complete_through  2026-09-03T15:10:00.000Z
job_id                       historical-market-recovery:aac843c098bae3a3
requested_start              2026-09-03T15:10:00.000Z
requested_end                2026-09-03T16:50:00.000Z
expected_bars                100
expected_success_version     8
```

This candidate is an implementation/review artifact only. A remote read-only
preflight must re-establish version 7 and all frozen identity before a separate
change window may authorize it.

## 4. Local acceptance

The focused continuation tests prove:

- omitted or malformed version/boundary headers fail before provider work;
- a supplied job ID that differs from deterministic replanning fails before a
  bar-provider call or D1 mutation;
- version 7 executes only the reviewed 100-bar next chunk;
- success advances only to version 8 / `2026-09-03T16:50:00.000Z`;
- replaying the version-7 request does not make a second provider call;
- the existing fixed first-chunk path remains accepted and replay-closed.

Acceptance commands and final counts are recorded in the integrated tracker.

```text
focused recovery/control tests     22 passed
full TypeScript suite              192 passed
TypeScript typecheck               passed
wrangler generated-type check      passed
live-canary deploy dry-run          passed
git diff check                      passed
remote writes                       none
```

## 5. Required remote sequence

Any later authorized window must preserve this order:

```text
read-only preflight
  -> safe deploy with gate false
  -> verify health and endpoint 404
  -> create temporary control secret
  -> temporarily deploy gate true
  -> verify unauthenticated 401
  -> send exactly one version-7 request
  -> immediately deploy gate false
  -> independently verify attempt, receipts, bars and checkpoint
  -> delete the temporary control secret
  -> verify final Shadow / News disabled / endpoint 404
```

Stop on any mismatch or non-success outcome. Do not retry in the same window
and do not widen the request, retention range, page limit or bar limit.
