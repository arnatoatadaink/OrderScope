# OrderScope — L1-003 PB-04 NVDA September 9 Remote Acceptance

Status: **ACCEPTED REMOTELY — PB-04 remains in progress**
Date: 2026-09-24 JST
Environment: `live-canary`

## Accepted campaign

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-09 REGULAR
evidence SHA-256   a0ac9c8aab46e9381982bb789c0c59463e536c6d19babf0457dff4dac13f86a2
checkpoint before  v18 / 2026-09-08T20:00:00.000Z
checkpoint after   v22 / 2026-09-09T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

Four independently verified chunks completed:

```text
1  13:30-15:10  100 inserted  v18 -> v19
2  15:10-16:50  100 inserted  v19 -> v20
3  16:50-18:30  100 inserted  v20 -> v21
4  18:30-20:00   90 inserted  v21 -> v22
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

PB-04 continues with September 10. Its frozen entry checkpoint is:

```text
version            22
complete through   2026-09-09T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

September 10 must be separately frozen and authorized. No later session is
implicitly authorized by this acceptance.
