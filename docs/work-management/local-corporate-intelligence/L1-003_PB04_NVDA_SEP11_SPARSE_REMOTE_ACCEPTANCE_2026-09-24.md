# OrderScope — L1-003 PB-04 NVDA September 11 Sparse Remote Acceptance

Status: **ACCEPTED REMOTELY — PB-04 remains in progress**
Date: 2026-09-24 JST
Environment: `live-canary`

## Accepted sparse campaign

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-11 REGULAR
evidence SHA-256   a41dcb05888182dada5dbde3fc420b74684abaac6e5f2aafcdb5fa81d8e8be90
checkpoint before  v26 / 2026-09-10T20:00:00.000Z
checkpoint after   v30 / 2026-09-11T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

Four independently verified chunks completed:

```text
1  13:30-15:10  100 inserted / absence 0  v26 -> v27
2  15:10-16:50  100 inserted / absence 0  v27 -> v28
3  16:50-18:30   99 inserted / absence 1  v28 -> v29
4  18:30-20:00   90 inserted / absence 0  v29 -> v30
```

The acknowledged provider absence was exactly:

```text
2026-09-11T16:57:00.000Z
```

This is recorded only as a reproducible provider absence. It does not assert
that no trade occurred at that timestamp.

All chunks returned `accepted=true`, `SUCCEEDED`, zero
conflict/rejected/missing. Persisted evidence inspection passed after every
chunk.

## Closeout

The temporary recovery gate was closed after the campaign, the temporary
`HISTORICAL_RECOVERY_CONTROL_TOKEN` was deleted, and the local-evidence
control endpoint returned HTTP 404. Worker remained Shadow and News remained
disabled.

## Next gate

PB-04 continues with September 14. Its frozen entry checkpoint is:

```text
version            30
complete through   2026-09-11T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

September 14 requires a separately frozen packet and separate authorization.
