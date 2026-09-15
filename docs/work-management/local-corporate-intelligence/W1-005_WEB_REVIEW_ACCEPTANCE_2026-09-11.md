# OrderScope — W1-005 Web Review Acceptance

Status: **Accepted — local/non-live boundary**
Date: 2026-09-11
Task: `W1-005 — Batch tiered Market acquisition by provider/cadence/range while preserving per-symbol coverage semantics`

## Review conclusion

The synced local acceptance evidence is sufficient to accept W1-005 for the reviewed local/non-live boundary.

Confirmed evidence:

- authoritative Universe remains `25 / 28 / 53 = 106`;
- compatible Market plans are deterministically batched by provider route, cadence, session scope, logical variant, acquisition mode, requested range, calendar revision, and Universe revision;
- per-symbol coverage/checkpoint/CAS semantics are retained;
- stock and crypto multi-symbol provider requests are supported by the implementation;
- checkpoint completion uses set-oriented D1 CAS with per-symbol version predicates;
- scheduler selects at most two compatible batch groups per tick in the checked-in local/shadow configuration;
- normal and shortened-session simulations meet the reviewed freshness targets;
- fail-before-crossing external/D1 budget behavior remains retained;
- no remote D1 mutation, Worker deployment, Cron change, Worker mode change, News live activation, or full-v0.1 live activation occurred.

## Capacity result

```text
Tier A max backlog age:            3 minutes
Tier B max backlog age:           17 minutes
1Min outstanding at close+30m:     0
15Min outstanding at close+30m:    0
1Day outstanding at deadline:      0
normal-day NEW bars:           11,581
shortened-day NEW bars:         6,925
selected batch groups/tick max:     2
reviewed external ceiling:         40
reviewed D1 ceiling:               40
```

Verification reported by Local:

```text
focused orchestration/capacity: 33 passed
full TypeScript suite:          124 passed
typecheck:                      passed
Wrangler typegen/dry-run:       passed
git diff --check:               passed
```

## W1-004 blocker disposition

The W1-004 blocker was specifically the one-instrument/one-job scheduler shape under `ACQUISITION_MAX_JOBS_PER_TICK=1`, which produced 69 minutes maximum Tier A backlog and outstanding 1Min work after close.

W1-005 replaces that capacity shape with bounded compatible multi-symbol batches and demonstrates the reviewed Tier A/Tier B/Tier C freshness targets in deterministic normal/shortened-session fixtures. The W1-004 scheduler-capacity blocker is therefore considered **resolved by W1-005 local evidence**.

W1-004 should now be reclassified from `Blocked` to `Resolved / superseded by W1-005 capacity evidence`, while retaining its original blocker report as historical evidence.

## Next gate

Proceed to the W1-001 Stage B final acceptance review using the consolidated evidence from W1-002 through W1-005.

Before any live Canary authorization, the final Stage B review must still distinguish local fixture evidence from live-only evidence. Live CPU time, provider paging distribution, scheduler jitter/delay, and real daily D1 row consumption remain later Canary observations.

No live infrastructure action is authorized by this acceptance.
