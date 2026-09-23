# OrderScope — L1-003 PB-01 Remote Read-only Preflight Reassessment

Status: **PASS — historical target moved to September 22 close**
Date: 2026-09-23 JST
Environment: `live-canary`

## 1. Read-only remote evidence

Operator evidence confirmed:

```text
Wrangler              authenticated after OAuth login
D1 control read        PASS
database               orderscope-state-live-canary
database id            03c85865-1aa3-4b0c-b219-18987cd260a6
coverage key           NVDA|1Min|REGULAR|stock:iex:raw
checkpoint version     18
complete through       2026-09-08T20:00:00.000Z
state                  COMPLETE
missing ranges         []
source observed through 2026-09-08T20:00:00.000Z
universe revision      stock-monitoring-canary-v0.1
blocker                null
retry not before       null
unresolved attempts    0
remote mutation        none
```

The remote checkpoint remains exactly the frozen PB-04 entry boundary required
for the September 9 campaign.

## 2. Moving-horizon reassessment

At approximately 2026-09-23 23:46 JST / 14:46 UTC, the 1,440-minute normal
provider retention floor is approximately:

```text
2026-09-22T14:46:00Z
```

September 22 Regular opened at 13:30 UTC. Therefore that session is no longer
wholly on or after the current retention floor.

The earliest authoritative Regular session wholly on or after the current
retention floor is September 23 Regular, so the PB-01 handoff boundary moves:

```text
previous historical target   2026-09-21T20:00:00Z
current historical target    2026-09-22T20:00:00Z
normal handoff candidate     2026-09-23 REGULAR
```

The accepted local provider bundle already contains September 22, so this
boundary movement does not require another provider collection.

## 3. PB-04 remaining sessions from remote checkpoint

Starting after the authoritative remote checkpoint at September 8 close, PB-04
must now make remote coverage contiguous through September 22 close:

```text
Sep 09
Sep 10
Sep 11
Sep 14
Sep 15
Sep 16
Sep 17
Sep 18
Sep 21
Sep 22
```

Ten local sessions are available. September 11 is the one reproducible sparse
IEX session and must use the accepted provider-absence evidence contract.

## 4. September 9 execution packet

The September 9 remote execution packet has been generated from the accepted
local dry-run and is frozen with:

```text
remote checkpoint       v18 / Sep 8 close
campaign session        Sep 9 Regular
chunk shape             100 / 100 / 100 / 90
expected checkpoint     v22 / Sep 9 close
authorization           false
remote mutation         not performed
```

The packet remains valid because the remote checkpoint exactly matches its
frozen entry identity. The moving historical target does not invalidate the
September 9 first-session campaign; it only extends the total PB-04 campaign
sequence through September 22.

## 5. Next gate

The next remote-mutating action is a separately authorized September 9 PB-04
change window. It must:

1. re-check the exact v18/Sep8 checkpoint immediately before mutation;
2. keep Worker Shadow and News disabled;
3. open only the historical-recovery control path required for one session;
4. execute four independent chunks with stop-after-each-chunk verification;
5. finish at v22/Sep9 close;
6. restore the false gate, delete the temporary control secret, and verify the
   endpoint returns 404;
7. perform final read-only D1 inspection.

No September 10 or later session is automatically authorized by a successful
September 9 campaign.
