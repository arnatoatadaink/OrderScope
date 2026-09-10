# OrderScope — W1-001 Stage B Tiered-Universe Blocker Report

Status: **Blocked — reference Universe contains 106 instruments, not 105**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Input: `W1-001_STAGE_B_TIERED_UNIVERSE_LOCAL_HANDOFF_2026-09-10.md`
Reference authority: `stock_monitoring_v0.1_universe_spec.md`

## 1. Decision

Stage B is **Blocked** at T1. The authoritative Universe specification and
`src/universe.ts` agree with each other, but they do not agree with the handoff's
required count oracle.

```text
                         1Min  15Min  1Day  Total
handoff expectation        25     28    52    105
reference specification    25     28    53    106
src/universe.ts             25     28    53    106
```

The extra count is not an implementation-only symbol. The reference specification
lists all three Storage instruments `WDC`, `STX`, and `SNDK`, and the implementation
faithfully includes all three at `1Day` cadence.

No Universe allocation was changed. Removing an unspecified Tier-C instrument to
force 105 would violate the instruction not to change allocation without a mismatch
against the reference specification.

## 2. Local evidence

The full-profile test now locks the exact reference-ordered symbol/cadence sequence,
not only aggregate counts. It also explicitly verifies the required representative
routes:

```text
NVDA    = 1Min stock
AMD     = 1Min stock
MRVL    = 15Min stock
MU      = 15Min stock
EWJ     = 1Day stock
TLT     = 1Day stock
BTCUSD  = 1Min crypto
ETHUSD  = 1Day crypto
```

## 3. Required disposition

Web review must choose and record one authoritative correction:

1. revise the handoff/budget model to `25 / 28 / 53 / 106`; or
2. revise `stock_monitoring_v0.1_universe_spec.md` to identify the specific Tier-C
   instrument removed from v0.1, then authorize the matching implementation change.

After that decision, rerun T1 and proceed with T2–T8 using the resolved Universe.
Workload, overlap, backlog, and daily-write projections were intentionally not
produced from an unresolved denominator.

## 4. Requested evidence

```text
W1-001 Stage B tiered-universe status: Blocked
Universe count 1Min: 25
Universe count 15Min: 28
Universe count 1Day: 53 (handoff requires 52)
Universe total: 106 (handoff requires 105)
normal-day planned bars 1Min: not measured — blocked at T1
normal-day planned bars 15Min: not measured — blocked at T1
normal-day planned bars 1Day: not measured — blocked at T1
normal-day NEW bars: not measured — blocked at T1
normal-day MATCHED/replayed observations: not measured — blocked at T1
normal-day Market row writes: not measured — blocked at T1
normal-day News row writes: not measured — blocked at T1
normal-day other Worker row writes: not measured — blocked at T1
normal-day total D1 row writes: not measured — blocked at T1
shortened-day total D1 row writes: not measured — blocked at T1
catch-up projection (separate): not measured — blocked at T1
normal combined external subrequests/tick: not measured — blocked at T1
worst combined external subrequests/tick: not measured — blocked at T1
normal combined D1 queries/tick: not measured — blocked at T1
worst combined D1 queries/tick: not measured — blocked at T1
max backlog age 1Min: not measured — blocked at T1
max backlog age 15Min: not measured — blocked at T1
max backlog age 1Day: not measured — blocked at T1
focused tests: 4 / 4 pass
full tests: 117 / 117 pass
typecheck: pass
wrangler dry-run/build: pass
git diff --check: pass
remote D1 applied: no
Worker deployed: no
Cron changed: no
Worker mode changed: no
```

Wrangler verification used a writable local `XDG_CONFIG_HOME` only to accommodate
its debug log; `wrangler deploy --dry-run` exited without deployment.
