# OrderScope — L1-003 NVDA Historical Recovery Continuation Handoff

Status: **ACCEPTED — version-7 continuation chunk completed remotely and gate removed**
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

## 6. Remote execution evidence

The reviewed commit `43cd1855e7cef9da53e40caf8ddc5bc5e7c185d7` was
already pushed and the worktree was clean before the 2026-09-17 JST change
window. The read-only preflight re-established the Cloudflare account, D1
target, Shadow mode, disabled News acquisition, and the exact version-7 NVDA
checkpoint with no missing ranges.

```text
19:14Z  continuation code deployed with HISTORICAL_RECOVERY_ENABLED=false
19:14Z  health returned 200 and disabled endpoint returned 404
19:15Z  temporary control secret created
19:16Z  temporary gate deployed; unauthenticated request returned 401
19:16Z  exactly one authenticated version-7 request returned HTTP 200
19:17Z  false-gate configuration restored
19:17Z  independent read-only D1 verification passed
19:17Z  temporary control secret deleted
19:18Z  final health 200; endpoint 404; secret absence verified
```

Invocation result:

```text
accepted                       true
outcome                        SUCCEEDED
job_id                         historical-market-recovery:aac843c098bae3a3
requested range                [2026-09-03T15:10:00.000Z, 16:50:00.000Z)
pages                          1
inserted / matched             100 / 0
conflicts / rejected / missing 0 / 0 / 0
external subrequests           1 of 40
D1 queries                     15 of 40
stopped_after_one_chunk        true
```

Independent D1 verification found exactly one SUCCEEDED attempt, 100 INSERTED
receipts, and 100 canonical NVDA bars from `2026-09-03T15:10:00.000Z`
through `2026-09-03T16:49:00.000Z`. The checkpoint is `COMPLETE`, has no
missing ranges or blocker, is complete through `2026-09-03T16:50:00.000Z`,
and is version 8. All verification statements reported zero writes.

Final safety state:

```text
deployment                     2c659f36-eb67-4d61-af0b-d87030993d21
Worker mode                    shadow
News                           disabled
HISTORICAL_RECOVERY_ENABLED    false
control endpoint               404
control secret                 deleted
```

## 7. Next gate

This window authorizes no automatic next chunk. Any version-8 continuation
must repeat the read-only preflight, deterministic next-job review, and
separately bounded one-chunk window. Normal-scheduler activation, Phase B,
direct D1 edits, and widened recovery bounds remain outside this acceptance.
