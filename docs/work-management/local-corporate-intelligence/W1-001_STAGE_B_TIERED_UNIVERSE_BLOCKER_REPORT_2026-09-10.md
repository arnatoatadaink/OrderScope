# OrderScope — W1-001 Stage B Tiered-Universe Blocker Report

Status: **Blocked — full-v0.1 checkpoint reads exceed the shared D1 ceiling**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Input: `W1-001_STAGE_B_TIERED_UNIVERSE_LOCAL_HANDOFF_2026-09-10.md`
Reference authority: `stock_monitoring_v0.1_universe_spec.md`

## 1. Universe decision resolved

Web review selected `25 / 28 / 53 = 106` as the authoritative v0.1 Universe.
The local handoff and budget revision now reflect that decision. The implementation
already matched it, so no instrument allocation changed.

The exact ordered symbol/cadence test and representative route test pass:

```text
NVDA    = 1Min stock       AMD     = 1Min stock
MRVL    = 15Min stock      MU      = 15Min stock
EWJ     = 1Day stock       TLT     = 1Day stock
BTCUSD  = 1Min crypto      ETHUSD  = 1Day crypto
```

## 2. New stop condition

Stage B remains **Blocked**, now at T7. Before scheduler selection or Market/News
acquisition, `runScheduledTick()` loads one checkpoint per Universe instrument:

```text
full-v0.1 instruments                 106
D1CoverageCheckpointPort.get calls   106
shared D1 query ceiling                40
ceiling exceeded by                    66
```

Each `get()` executes one `SELECT ... WHERE coverage_key = ?` statement. This is
already 106 D1 queries before lease, attempt, bar persistence, checkpoint CAS,
stale-attempt summary, News, or digest statements. It therefore violates the
explicit `combined D1 queries <= 40` stop condition without needing a remote D1 or
traffic estimate.

The existing shared `InvocationBudget` is created only after these reads and
`worker.ts` still publishes `marketD1Queries: null` and `totalD1Queries: null`.
That observability gap does not make the reads free; it confirms that the current
digest understates the protected invocation path.

## 3. Reproduction evidence

`loadMarketCheckpoints()` was extracted without changing behavior so the real
full-profile fan-out can be tested directly. The fixture proves 106 unique point
reads and verifies stock and crypto coverage-key construction.

The production-safe remediation requires a reviewed, bounded bulk checkpoint read
(for example one set-oriented query for the full requested coverage-key set), then
shared budget instrumentation around every actual Market/News D1 statement. The
tiered workload and daily-write fixtures should resume only after that prerequisite
keeps the entire invocation at or below 40.

No setting was increased, Market guarantee weakened, or live action taken.

## 4. Requested evidence

```text
W1-001 Stage B tiered-universe status: Blocked
Universe count 1Min: 25
Universe count 15Min: 28
Universe count 1Day: 53
Universe total: 106
normal-day planned bars 1Min: not measured — blocked at T7 pre-acquisition reads
normal-day planned bars 15Min: not measured — blocked at T7 pre-acquisition reads
normal-day planned bars 1Day: not measured — blocked at T7 pre-acquisition reads
normal-day NEW bars: not measured — blocked at T7 pre-acquisition reads
normal-day MATCHED/replayed observations: not measured — blocked at T7 pre-acquisition reads
normal-day Market row writes: not measured — blocked at T7 pre-acquisition reads
normal-day News row writes: not measured — blocked at T7 pre-acquisition reads
normal-day other Worker row writes: not measured — blocked at T7 pre-acquisition reads
normal-day total D1 row writes: not measured — blocked at T7 pre-acquisition reads
shortened-day total D1 row writes: not measured — blocked at T7 pre-acquisition reads
catch-up projection (separate): not measured — blocked at T7 pre-acquisition reads
normal combined external subrequests/tick: not measured — blocked before acquisition
worst combined external subrequests/tick: not measured — blocked before acquisition
normal combined D1 queries/tick: >= 106 before acquisition
worst combined D1 queries/tick: >= 106 before acquisition
max backlog age 1Min: not measured — blocked at T7
max backlog age 15Min: not measured — blocked at T7
max backlog age 1Day: not measured — blocked at T7
focused tests: 8 / 8 pass
full tests: 118 / 118 pass
typecheck: pass
wrangler dry-run/build: pass
git diff --check: pass
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```
