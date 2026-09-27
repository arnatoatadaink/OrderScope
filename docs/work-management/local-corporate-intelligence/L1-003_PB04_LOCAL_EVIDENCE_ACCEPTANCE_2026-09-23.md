# OrderScope — L1-003 PB-04 Local Evidence Import Acceptance

Status: **ACCEPTED LOCALLY — remote mutation not authorized**
Date: 2026-09-23 JST
Branch: `l1-003-local-market-recovery`

## 1. Scope

Accept the local-evidence import contract and the September 9 PB-04 dry-run /
executor simulation boundary without mutating remote D1, Worker, Cron, secrets,
or checkpoint state.

## 2. Accepted evidence

Local evidence contract:

- v3 session SHA-256 is verified;
- validation is recomputed from bars and must match stored validation;
- structurally invalid evidence is rejected;
- sparse evidence must be reproducible;
- reproducible provider absence is coverage evidence only, never a synthetic bar;
- ordinary unacknowledged gaps remain PARTIAL and stop checkpoint progression;
- zero absence count does not change the legacy acquisition-summary shape.

September 9 dry-run:

```text
session                2026-09-09
checkpoint before      v18 / 2026-09-08T20:00:00.000Z
chunks                 4
shape                  100 / 100 / 100 / 90
remoteMutation         false
expected checkpoint    v22 / 2026-09-09T20:00:00.000Z
```

Executor simulation:

```text
Local JSON
  -> local fetchPage adapter
  -> executeAcquisitionJob
  -> normalize
  -> acceptance
  -> missing evaluation
  -> checkpoint CAS-equivalent in-memory progression
```

Acceptance evidence supplied by the operator:

```text
focused tests          17 passed / 17
TypeScript typecheck   passed
git diff --check       clean
```

## 3. Boundary

This acceptance does not authorize remote D1 write, Worker deployment, secret
mutation, historical endpoint activation, Cron mutation, or checkpoint movement.

The authoritative remote checkpoint remains:

```text
NVDA|1Min|REGULAR|stock:iex:raw
version                18
complete through       2026-09-08T20:00:00.000Z
state                  COMPLETE
```

## 4. Next gate

Before a remote September 9 PB-04 change window:

1. rerun PB-01 read-only moving-horizon preflight;
2. confirm remote checkpoint is still exactly v18 / Sep8 close and clean;
3. freeze current Worker/config/calendar/Universe identity;
4. generate the September 9 remote execution packet from the accepted local
   evidence SHA-256 and four frozen chunk identities;
5. review stop/rollback criteria;
6. obtain a distinct remote mutation authorization.

If any remote identity or checkpoint differs, stop and regenerate the packet.
