# OrderScope — L1-003 PB-04 September 14 Change-window Authorization

Status: **AUTHORIZED — execution pending operator invocation**
Date: 2026-09-24 JST
Environment: `live-canary`

## Authorized scope

This authorization covers exactly one remote-mutating PB-04 campaign:

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-14 REGULAR
checkpoint entry   v30 / 2026-09-11T20:00:00.000Z
checkpoint target  v34 / 2026-09-14T20:00:00.000Z
chunk count        4
remote target      live-canary only
```

No September 15 or later session is authorized by this record.

## Frozen evidence

```text
provider bars      390
expected grid      390
acknowledged gap   0
evidence SHA-256   d8e608efbedbef1c0657de01709ce7cfda594d3108355724c26bf56cee68fa55
recovery id        L1-003-NVDA-20260914-LOCAL
```

## Frozen chunks

```text
1  13:30-15:10  100 provider bars  v30 -> v31
2  15:10-16:50  100 provider bars  v31 -> v32
3  16:50-18:30  100 provider bars  v32 -> v33
4  18:30-20:00   90 provider bars  v33 -> v34
```

## Preconditions accepted

```text
focused tests           18/18 PASS
TypeScript              PASS
git diff --check        clean
local dry-run           PASS / 4 chunks
remote packet           FROZEN / NOT AUTHORIZED in packet
remote checkpoint       v30 / Sep11 close / COMPLETE
missing ranges          []
blocker                 null
unresolved attempts     0
expected checkpoint     exact assertion = 1
```

## Required execution behavior

Use only:

```bash
bash scripts/l1_003_pb04_sep14_change_window.sh
```

The script must stop on any packet drift, evidence mismatch, checkpoint drift,
persistence mismatch, authorization failure, or unexpected HTTP status. It
must restore the checked-in false gate and delete the temporary control secret
on exit.

Successful acceptance requires all four chunks to pass, followed by a final
checkpoint of exactly v34 / 2026-09-14T20:00:00.000Z / COMPLETE / no missing
ranges / no blocker, and endpoint HTTP 404 after safe-close.
