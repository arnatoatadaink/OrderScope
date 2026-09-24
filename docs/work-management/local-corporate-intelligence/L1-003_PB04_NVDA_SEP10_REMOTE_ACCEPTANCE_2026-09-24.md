# OrderScope — L1-003 PB-04 NVDA September 10 Remote Acceptance

Status: **ACCEPTED REMOTELY — PB-04 remains in progress**
Date: 2026-09-24 JST
Environment: `live-canary`

## Accepted campaign

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-10 REGULAR
evidence SHA-256   a6c9ee21c136303e41010434e27b5fd469e8c2f080a1c290449bb46d06ddfb19
checkpoint before  v22 / 2026-09-09T20:00:00.000Z
checkpoint after   v26 / 2026-09-10T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

Four independently verified chunks completed:

```text
1  13:30-15:10  100 inserted  v22 -> v23
2  15:10-16:50  100 inserted  v23 -> v24
3  16:50-18:30  100 inserted  v24 -> v25
4  18:30-20:00   90 inserted  v25 -> v26
```

All chunks returned `accepted=true`, `SUCCEEDED`, zero conflict/rejected/missing,
and zero acknowledged absence. Persisted evidence inspection passed after every
chunk.

## Closeout

The temporary recovery gate was closed after the campaign, the temporary
`HISTORICAL_RECOVERY_CONTROL_TOKEN` was deleted, and the local-evidence
control endpoint returned HTTP 404. Worker remained Shadow and News remained
disabled.

## Next gate

PB-04 continues with September 11. Its frozen entry checkpoint is:

```text
version            26
complete through   2026-09-10T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

September 11 is the reproducible sparse IEX session with one explicit absence at
`2026-09-11T16:57:00.000Z`. It requires the sparse-evidence path and separate
authorization.
