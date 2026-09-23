# OrderScope — L1-003 Local NVDA Historical Collection Handoff

Status: **LOCAL COLLECTION ACCEPTED — import not authorized**
Date: 2026-09-23 JST
Branch: `l1-003-local-market-recovery`
Parent: `L1-003_PHASE_B_START_READINESS_WBS_CP_2026-09-18.md`

## 1. Purpose

Collect the remaining historical NVDA Regular-session minute bars locally without
deploying a Worker, mutating D1, moving a checkpoint, changing a secret, or
activating Cron.

This is a collection/evidence step only. It does not itself satisfy PB-04,
PB-05, PB-06, or authorize Phase B.

## 2. Default bounded scope

The default collection set is deliberately frozen to the completed Regular
sessions after the accepted September 8 checkpoint and before the intended
normal-scheduler handoff candidate:

```text
2026-09-09
2026-09-10
2026-09-11
2026-09-14
2026-09-15
2026-09-16
2026-09-17
2026-09-18
2026-09-21
```

Expected total:

```text
9 sessions x 390 bars = 3,510 one-minute bars
coverage = NVDA|1Min|REGULAR|stock:iex:raw
```

September 22 is intentionally not part of the default historical bundle. It is
reserved as the candidate normal-retention handoff session and must be
re-evaluated by the current PB-01 moving-horizon preflight before any checkpoint
or scheduler action.

## 3. Implementation

`scripts/l1_003_collect_nvda_local.ts`

- reuses the existing `fetchHistoricalBars` Alpaca adapter;
- uses feed `iex`, adjustment `raw`, cadence `1Min`;
- performs no D1, Worker, Cron, secret, or checkpoint mutation;
- retries bounded transient provider failures;
- writes only below `var/l1-003/local-market-recovery/nvda/`, which is ignored
  by Git;
- emits one JSON evidence file per session plus `manifest.json`.

`src/local-history-collector.ts`

- converts New York 09:30–16:00 Regular windows to canonical UTC, including DST;
- validates 390 bars per full Regular session;
- rejects duplicate timestamps and out-of-range timestamps.

## 4. Local execution

First inspect the frozen plan without credentials or network access:

```bash
node --experimental-strip-types scripts/l1_003_collect_nvda_local.ts --dry-plan
```

Then provide the same Alpaca credential names already used by the Worker:

```bash
export ALPACA_API_KEY='...'
export ALPACA_API_SECRET='...'

node --experimental-strip-types scripts/l1_003_collect_nvda_local.ts
```

A different bounded set can be selected explicitly:

```bash
node --experimental-strip-types scripts/l1_003_collect_nvda_local.ts \
  --session 2026-09-09 \
  --session 2026-09-10
```

## 5. Acceptance rule

Local collection uses provider-aware acceptance:

```text
denseSession       every expected clock minute has a provider bar
structurallyValid  no duplicate/out-of-range bars and all absent minutes are explicit
accepted           structurallyValid AND (denseSession OR reproducible=true)
```

Missing bars are never synthesized. A sparse provider session requires a second
identical retrieval with the same deterministic content SHA-256 before it is
accepted.

## 6. Verification performed during implementation

The session planning/validation logic was exercised independently with Node
type stripping:

```text
September EDT window  09:30 America/New_York -> 13:30Z
winter EST window     09:30 America/New_York -> 14:30Z
390 unique in-range bars -> complete=true
```

Network collection was not executed from the development environment because
the local Alpaca credentials are intentionally not available there.

## 7. Next boundary

After the local manifest reports PASS:

1. preserve the collected files as local evidence;
2. rerun PB-01 read-only preflight against current time;
3. confirm the actual historical handoff boundary;
4. compare the collected range to that boundary;
5. design/review an import path that preserves the existing accepted-record and
   checkpoint-CAS contracts;
6. only then consider D1/checkpoint mutation under a separate authorization.

Do not advance the existing checkpoint merely because the local files exist.


## 8. 2026-09-23 sparse-session reconciliation

Repeated local retrieval of the September 11 IEX Regular session produced the
same provider dataset:

```text
bars              389
missing minute    2026-09-11T16:57:00.000Z
content SHA-256   9d810707c426e25282ca6b3be9372378076563c06e9bc2492606c51540f154c4
reproducible      true
```

The local acceptance model is therefore revised so that a provider session is
not required to be artificially dense. Validation now separates:

```text
denseSession       every expected clock minute has a provider bar
structurallyValid  no duplicate/out-of-range bars and all absent minutes are explicit
accepted           structurallyValid AND (denseSession OR reproducible=true)
```

No missing minute is synthesized. A sparse session is accepted only after the
same complete provider payload is retrieved again with an identical
deterministic content hash.

Because the validation schema contributes to the deterministic hash, the first
run after this schema revision will establish a new v3 hash and may report
`reproducible=false`. A second identical run is required to establish
`reproducible=true` under the revised schema.


## 9. Final local collection acceptance

The full nine-session v3 collection completed with every session accepted.

```text
2026-09-09  390 bars  dense=true   accepted=true
2026-09-10  390 bars  dense=true   accepted=true
2026-09-11  389 bars  dense=false  accepted=true  reproducible=true
2026-09-14  390 bars  dense=true   accepted=true
2026-09-15  390 bars  dense=true   accepted=true
2026-09-16  390 bars  dense=true   accepted=true
2026-09-17  390 bars  dense=true   accepted=true
2026-09-18  390 bars  dense=true   accepted=true
2026-09-21  390 bars  dense=true   accepted=true
```

Aggregate provider bars: **3,509**. The one explicit sparse minute is
`2026-09-11T16:57:00.000Z`. The September 11 v3 content SHA-256 is
`a41dcb05888182dada5dbde3fc420b74684abaac6e5f2aafcdb5fa81d8e8be90`
and was reproduced exactly on the second retrieval.

Final disposition:

```text
local collection       ACCEPTED
remote mutation        none
D1 import              NOT AUTHORIZED
checkpoint             unchanged remotely
PB-04                  still IN PROGRESS remotely
PB-05                  still BLOCKED remotely
```

The local bundle is now suitable as reviewed input to a separately designed
import path. It does not itself move the remote checkpoint.
