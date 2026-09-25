# OrderScope — L1-003 PB-08 Sep25 Regular Frontier Re-freeze

Status: **LOCAL VALIDATION REQUIRED / REMOTE NOT AUTHORIZED**
Date: 2026-09-26 JST
Branch: `l1-003-local-market-recovery`

## Fresh read-only basis

Observed snapshot:

```text
observed_now=2026-09-25T22:14:11.000Z
remoteMutation=false

NVDA  v61 COMPLETE 2026-09-23T18:28:00.000Z
AMD   v43 COMPLETE 2026-09-24T14:50:00.000Z
QQQ   v12 COMPLETE 2026-09-24T14:33:00.000Z
SPY   v44 COMPLETE 2026-09-24T15:10:00.000Z
BTCUSD v49 COMPLETE 2026-09-24T08:13:00.000Z
unresolved NVDA attempts=0
Worker=shadow
News=disabled
feed=iex
```

At this snapshot the 1440-minute retention floor is approximately
`2026-09-24T22:14:11Z`, so all of Sep24 Regular is expired.
The correct next authoritative equity session is therefore Sep25 Regular.

## Frozen catch-up packet

```text
entry:
  NVDA version=61
  completeThrough=2026-09-23T18:28:00.000Z

target:
  NVDA version=65
  completeThrough=2026-09-25T20:00:00.000Z

expected clean NVDA jobs:
  1. 100 accepted bars
  2. 100 accepted bars
  3. 100 accepted bars
  4.  93 accepted bars

max scheduler opportunities:
  16
```

The overlap semantics permit matched bars inside each request; the accepted
total per job is inserted + matched.

## Retention guard

The packet is valid only while the moving 1440-minute retention floor has not
passed Sep25 Regular open:

```text
2026-09-25T13:30:00.000Z
```

Operationally this is approximately until 2026-09-26 22:30 JST.

## Acceptance

All NVDA attempts in the change window must be SUCCEEDED with:
- conflicts=0
- rejected=0
- missing=0

Final checkpoint must be:

```text
version=65
completeThrough=sourceObservedThrough=2026-09-25T20:00:00.000Z
state=COMPLETE
missing=[]
blocker=null
retry_not_before=null
```

PB-09/PB-10 remain outside this packet.
