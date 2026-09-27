# UWBS-086 — Historical / Capacity Evidence Gap — 2026-09-27

Status: **HISTORICAL EVIDENCE PENDING / CAPACITY MODEL READY**
Branch: `l1-003-local-market-recovery`

## 1. Purpose

This record prevents synthetic regression fixtures from being misrepresented as historical Canary evidence.

UWBS-086 has an accepted software contract and now has a deterministic replay/capacity evaluator, but final historical/capacity acceptance remains open.

## 2. Accepted software boundary

Local acceptance already established:

```text
cross-asset Canary focused tests: 8 passed
full Python regression:         770 passed
compileall:                     PASS
git diff --check:               PASS
```

The base decision policy remains:

```text
capacity headroom below threshold -> REJECT
false negative                    -> REJECT
regime mismatch                   -> REJECT
false positive                    -> REVIEW
clean replay + headroom           -> ACCEPT
```

## 3. Replay/capacity evaluator added

`analysis/app/orderscope_local/cross_market/cross_asset_canary_replay.py`

The evaluator:

- accepts projected Worker/D1 usage and an externally supplied capacity envelope;
- computes conservative headroom from the most constrained supplied resource;
- keeps platform quotas out of domain constants;
- distinguishes Cron-trigger-count limits from daily scheduled invocations;
- preserves synthetic replay scenarios as synthetic-only regression data.

Focused tests:

`analysis/tests/cross_market/test_cross_asset_canary_replay.py`

## 4. Current repository-grounded capacity facts

Current checked-in Worker configuration uses one cron expression:

```text
* * * * *
```

which corresponds to 1,440 scheduled Worker executions per 24-hour day when continuously enabled.

The Worker-side invocation budget currently caps:

```text
external subrequests per invocation: 40
D1 query executions per invocation:  40
```

Therefore a deliberately conservative execution-count ceiling is:

```text
1,440 invocations/day * 40 D1 executions/invocation = 57,600 D1 executions/day
```

This number is **not** a D1 row-write estimate. A query may read/write zero, one or multiple rows, and the budget wrapper charges statement execution rather than Cloudflare billing rows.

Consequently the repository alone does not yet prove compliance with the D1 Free `rows_written/day` or `rows_read/day` limits.

## 5. Fresh platform planning envelope

As of 2026-09-27, current Cloudflare documentation gives the following Workers Free / D1 Free planning limits:

```text
Workers requests:       100,000/day
D1 rows read:         5,000,000/day
D1 rows written:        100,000/day
D1 maximum DB size:         500 MB
D1 account storage:           5 GB
D1 queries/Worker invocation: 50 (Free platform limit)
Cron triggers/account:         5
```

OrderScope's internal D1 execution ceiling of 40/invocation is below the platform's 50-query Free limit.

The Cloudflare quota values above are planning evidence only and are not hard-coded into the domain contract.

## 6. Historical evidence audit

The active branch contains unit/integration fixtures, accepted market-recovery evidence and planning reports, but this audit has not established a repository-backed historical dataset that simultaneously supplies the canonical UWBS-080..085 inputs needed to replay an oil/BTC cross-asset regime episode end to end.

Therefore:

- synthetic `broad-risk-on`, `crypto-only`, and `noise` fixtures remain regression fixtures only;
- no false-positive / false-negative rate may be claimed as historical calibration from those fixtures;
- UWBS-086 must not be marked fully Accepted yet.

## 7. Final acceptance prerequisites

Final UWBS-086 acceptance requires at least:

1. local verification of the replay/capacity evaluator;
2. one or more repository-backed historical cross-asset replay packets with expected labels defined independently of the classifier under test;
3. replay summary with false positives, false negatives and regime mismatches;
4. measured or defensibly bounded D1 `rows_read`, `rows_written`, and storage growth for the intended schedule;
5. Worker request usage projection;
6. capacity headroom calculation against a fresh platform envelope;
7. final `ACCEPT / REVIEW / REJECT` decision.

## 8. Safe close

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution or trading action was performed for this audit.
