# OrderScope — L1-003 PB-04 September 11 Sparse Change-window Authorization

Status: **AUTHORIZED — execution pending operator invocation**
Date: 2026-09-24 JST
Environment: `live-canary`

## Authorized scope

This authorization covers exactly one remote-mutating PB-04 campaign:

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-11 REGULAR
checkpoint entry   v26 / 2026-09-10T20:00:00.000Z
checkpoint target  v30 / 2026-09-11T20:00:00.000Z
chunk count        4
remote target      live-canary only
```

No September 14 or later session is authorized by this record.

## Sparse evidence identity

```text
provider bars      389
expected grid      390
acknowledged gap   1
gap timestamp      2026-09-11T16:57:00.000Z
evidence SHA-256   a41dcb05888182dada5dbde3fc420b74684abaac6e5f2aafcdb5fa81d8e8be90
recovery id        L1-003-NVDA-20260911-LOCAL
```

The absence is treated only as a reproducible provider absence. This record
does not assert that no trade occurred at that timestamp.

## Frozen chunks

```text
1  13:30-15:10  100 provider bars / 0 absence  v26 -> v27
2  15:10-16:50  100 provider bars / 0 absence  v27 -> v28
3  16:50-18:30   99 provider bars / 1 absence  v28 -> v29
4  18:30-20:00   90 provider bars / 0 absence  v29 -> v30
```

Frozen job IDs:

```text
historical-market-recovery:041b8b3015f77549
historical-market-recovery:f7849cba75d95db0
historical-market-recovery:afc4d4b87713cb0b
historical-market-recovery:54517a3e5ba877a5
```

## Preconditions accepted

```text
local sparse tests      18/18 PASS
TypeScript              PASS
git diff --check        clean
local dry-run           PASS / 4 chunks
remote packet           FROZEN / NOT AUTHORIZED in packet
remote checkpoint       v26 / Sep10 close / COMPLETE
missing ranges          []
blocker                 null
unresolved attempts     0
expected checkpoint     exact assertion = 1
```

## Required execution behavior

Use only:

```bash
bash scripts/l1_003_pb04_sep11_change_window.sh
```

The script must stop on any packet drift, evidence mismatch, checkpoint drift,
unexpected sparse accounting, persistence mismatch, authorization failure, or
unexpected HTTP status. It must restore the checked-in false gate and delete
the temporary control secret on exit.

Successful acceptance requires all four chunks to pass, including chunk 3 with
99 provider bars plus exactly one acknowledged absence, followed by a final
checkpoint of exactly v30 / 2026-09-11T20:00:00.000Z / COMPLETE / no missing
ranges / no blocker, and endpoint HTTP 404 after safe-close.
