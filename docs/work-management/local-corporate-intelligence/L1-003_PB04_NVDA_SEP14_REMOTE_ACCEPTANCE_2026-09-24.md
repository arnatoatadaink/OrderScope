# OrderScope — L1-003 PB-04 NVDA September 14 Remote Acceptance

Status: **ACCEPTED REMOTELY — PB-04 remains in progress**
Date: 2026-09-24 JST
Environment: `live-canary`

## Accepted campaign

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-14 REGULAR
evidence SHA-256   d8e608efbedbef1c0657de01709ce7cfda594d3108355724c26bf56cee68fa55
checkpoint before  v30 / 2026-09-11T20:00:00.000Z
checkpoint after   v34 / 2026-09-14T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

Four independently verified chunks completed:

```text
1  13:30-15:10  100 inserted / absence 0  v30 -> v31
2  15:10-16:50  100 inserted / absence 0  v31 -> v32
3  16:50-18:30  100 inserted / absence 0  v32 -> v33
4  18:30-20:00   90 inserted / absence 0  v33 -> v34
```

All chunks returned `accepted=true`, `SUCCEEDED`, zero
conflict/rejected/missing. Persisted evidence inspection passed after every
chunk.

The first chunk observed two bounded HTTP 404 rollout retries before the
new authenticated endpoint became reachable. The request was then accepted;
no widening of the retry policy was required.

## Closeout

The temporary recovery gate was closed after the campaign, the temporary
`HISTORICAL_RECOVERY_CONTROL_TOKEN` was deleted, and the local-evidence
control endpoint returned HTTP 404. Worker remained Shadow and News remained
disabled.

## Next gate

PB-04 continues from:

```text
version            34
complete through   2026-09-14T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            none
```

Any multi-session closeout preparation must preserve the per-session,
four-chunk, checkpoint-CAS, persisted-evidence and safe-close boundaries.
PB-05 and PB-06 remain separately gated.
