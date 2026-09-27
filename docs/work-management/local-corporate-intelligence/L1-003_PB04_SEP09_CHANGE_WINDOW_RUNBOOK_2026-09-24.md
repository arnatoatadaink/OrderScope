# OrderScope — L1-003 PB-04 September 9 Change-window Runbook

Status: **AUTHORIZED BY OPERATOR — execution pending local invocation**
Date: 2026-09-24 JST
Environment: `live-canary`
Scope: September 9 NVDA Regular session only

## Frozen entry identity

```text
coverage key       NVDA|1Min|REGULAR|stock:iex:raw
checkpoint         v18
complete through   2026-09-08T20:00:00.000Z
state              COMPLETE
missing ranges     []
blocker            null
unresolved attempts 0
universe revision  stock-monitoring-canary-v0.1
```

## Frozen local evidence

```text
market date        2026-09-09
session            13:30Z -> 20:00Z
provider           alpaca-stock-bars-v1 / IEX raw
bars               390
SHA-256            a0ac9c8aab46e9381982bb789c0c59463e536c6d19babf0457dff4dac13f86a2
recovery id        L1-003-NVDA-20260909-LOCAL
calendar revision  local-evidence:2026-09-09
```

The temporary Worker path is hard-bound to the values above. It cannot accept a
different date, evidence hash, checkpoint boundary, recovery id, or calendar
revision.

## Execution path

```text
checked-in safe baseline (gate=false)
  -> local tests / typecheck / diff check
  -> live health + endpoint 404 check
  -> exact read-only D1 checkpoint check
  -> temporary control secret
  -> temporary gate=true deploy
  -> endpoint must return 401 without token
  -> chunk 1 -> response verification -> D1 inspection
  -> chunk 2 -> response verification -> D1 inspection
  -> chunk 3 -> response verification -> D1 inspection
  -> chunk 4 -> response verification -> D1 inspection
  -> require v22 / Sep9 close / COMPLETE
  -> deploy checked-in gate=false
  -> delete temporary control secret
  -> endpoint expected 404
```

The operator entrypoint is:

```bash
bash scripts/l1_003_pb04_sep09_change_window.sh
```

It requires `ORDERSCOPE_LIVE_CANARY_URL` to be set to the live-canary Worker
base URL. The script refuses to start with a dirty worktree, wrong branch,
wrong packet/evidence identity, non-shadow Worker, active News, checkpoint
drift, unresolved acquisition attempt, or an already-open control endpoint.

## Fail-closed behavior

The shell EXIT/INT/TERM trap attempts safe-close even when any chunk or
verification fails. A failed campaign must not continue to the next chunk.

The remote execution packet must be regenerated after the recovery-id
preservation fix. A packet whose recovery id differs from
`L1-003-NVDA-20260909-LOCAL` is rejected before mutation.

## Acceptance target

```text
chunk shape         100 / 100 / 100 / 90
conflicts           0
rejected            0
missing             0
checkpoint versions 18 -> 19 -> 20 -> 21 -> 22
final through        2026-09-09T20:00:00.000Z
final state          COMPLETE
```

This authorization covers September 9 only. September 10 and later sessions
require a separately frozen control identity and change window.
