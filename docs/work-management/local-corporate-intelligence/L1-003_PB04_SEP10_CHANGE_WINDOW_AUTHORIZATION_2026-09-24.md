# OrderScope — L1-003 PB-04 September 10 Change-window Authorization

Status: **AUTHORIZED — execution pending operator invocation**
Date: 2026-09-24 JST
Environment: `live-canary`

## Authorized scope

This authorization covers exactly one remote-mutating PB-04 campaign:

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
session            2026-09-10 REGULAR
checkpoint entry   v22 / 2026-09-09T20:00:00.000Z
checkpoint target  v26 / 2026-09-10T20:00:00.000Z
chunk count        4
remote target      live-canary only
```

No September 11 or later session is authorized by this record.

## Preconditions already accepted

```text
local dry-run       PASS
remote packet       FROZEN
focused tests       17/17 PASS
TypeScript          PASS
git diff --check    clean
remote checkpoint   v22 / Sep9 close / COMPLETE
missing ranges      []
blocker             null
unresolved attempts 0
```

## Frozen evidence

```text
market date        2026-09-10
provider bars      390
SHA-256            a6c9ee21c136303e41010434e27b5fd469e8c2f080a1c290449bb46d06ddfb19
recovery id        L1-003-NVDA-20260910-LOCAL
```

## Required execution behavior

The operator must use:

```bash
bash scripts/l1_003_pb04_sep10_change_window.sh
```

The script must stop on any non-accepted chunk, checkpoint drift, persistence
mismatch, authorization failure, or unexpected HTTP status. It must restore the
checked-in false gate and delete the temporary control secret on exit.

Successful acceptance requires all four chunks to pass and the final checkpoint
to be exactly v26 / 2026-09-10T20:00:00.000Z / COMPLETE / no missing ranges /
no blocker, followed by endpoint HTTP 404 after safe-close.
