# OrderScope — L1-003 NVDA Version-8 / Version-9 Recovery Closeout

Status: **ACCEPTED — both one-shot windows succeeded; gates removed and safe baseline verified**
Date: 2026-09-18 JST
Parent: `L1-003_NVDA_HISTORICAL_RECOVERY_CONTINUATION_HANDOFF_2026-09-16.md`
Environment: `live-canary`

## 1. Purpose and boundary

Record the two remotely completed continuation windows after checkpoint version
8. These executions are prerequisite historical-recovery evidence. They do not
authorize another recovery chunk, normal-scheduler activation, or Phase B.

## 2. Version-8 one-shot result

```text
recovery_id                  L1-003-NVDA-20260916-01
job_id                       historical-market-recovery:75cf6e5907896220
checkpoint before            version 8 / 2026-09-03T16:50:00.000Z
requested range              [2026-09-03T16:50:00.000Z, 18:30:00.000Z)
expected / accepted bars     100 / 100
pages                        1
inserted / matched           100 / 0
conflicts/rejected/missing   0 / 0 / 0
external / D1 operations     1 / 15
checkpoint after             COMPLETE / no gaps / version 9
complete through             2026-09-03T18:30:00.000Z
started / finished           2026-09-17T07:19:49.985Z / 07:19:52.552Z
stopped after one chunk      true
```

Independent read-only verification found one successful attempt, 100 INSERTED
receipts, and 100 canonical bars through `2026-09-03T18:29:00.000Z`.

The temporary gate version was
`25c7d9ff-8354-4dff-9a3c-adc127eecb93`. The immediate false-gate deployment
was `166cbb00-11dc-45b5-9909-dad7f8971c0d`, and the temporary control secret
was deleted.

## 3. Version-9 one-shot result

```text
recovery_id                  L1-003-NVDA-20260916-01
job_id                       historical-market-recovery:74025ff8e1e78c42
checkpoint before            version 9 / 2026-09-03T18:30:00.000Z
requested range              [2026-09-03T18:30:00.000Z, 20:00:00.000Z)
expected / accepted bars     90 / 90
pages                        1
inserted / matched           90 / 0
conflicts/rejected/missing   0 / 0 / 0
external / D1 operations     1 / 15
checkpoint after             COMPLETE / no gaps / version 10
complete through             2026-09-03T20:00:00.000Z
started / finished           2026-09-17T14:43:17.528Z / 14:43:35.721Z
stopped after one chunk      true
```

Independent read-only verification found one successful attempt, 90 INSERTED
receipts, and 90 canonical bars from `2026-09-03T18:30:00.000Z` through
`2026-09-03T19:59:00.000Z`.

The safe pre-deployment was
`8a54ab5b-4ea3-4eec-9144-ad5fe4631091`, the temporary gate version was
`b1e2ae08-749f-466a-aa2e-3ca8d025363f`, and the immediate false-gate
deployment was `75afb507-a7e4-409a-982a-6e09f15ce7ec`. The temporary control
secret was deleted.

## 4. 2026-09-18 reconciliation

Read-only reconciliation at `2026-09-17T18:36:43Z` confirmed:

```text
NVDA checkpoint              version 10 / COMPLETE / no gaps
complete/source through      2026-09-03T20:00:00.000Z
version-9 job receipts       90 INSERTED / no other outcome
Worker health                HTTP 200 / shadow
News                         disabled
historical recovery endpoint HTTP 404
control secret               absent
latest deployment source     secret deletion
latest deployment version    369c4cdc-ef87-42b7-aa43-e806c862973c
```

The latest version differs from the immediate false-gate deployment because
deleting the secret creates a new Worker version. This is the expected final
safe state, not an additional recovery execution.

## 5. Disposition

Both windows are accepted. The contiguous accepted-record chain now reaches
the September 3 Regular close. Phase B remains **NOT READY** because this
checkpoint is outside the normal scheduler's 24-hour retention horizon and no
normal-scheduler handoff or current-session stability observation has occurred.

The next authority boundary is the WBS/critical path in
`L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`.
