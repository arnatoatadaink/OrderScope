# UWBS-086 — Historical / Capacity Evidence Gap — 2026-09-27

Status: **HISTORICAL EVIDENCE PENDING / EXTENDED CAPACITY MODEL LOCAL VERIFICATION REQUIRED**
Branch: `l1-003-local-market-recovery`

## 1. Purpose

This record prevents synthetic regression fixtures from being misrepresented as historical Canary evidence and keeps Cloudflare statement-count budgeting separate from D1 billing-row capacity evidence.

UWBS-086 has an accepted base software contract and deterministic replay/capacity evaluator. Final historical/capacity acceptance remains open.

## 2. Accepted base software boundary

Local acceptance already established:

```text
cross-asset Canary focused tests:  8 passed
replay/capacity focused tests:     10 passed
full Python regression:           780 passed
compileall:                        PASS
git diff --check:                  PASS
```

The base decision policy remains:

```text
capacity headroom below threshold -> REJECT
false negative                    -> REJECT
regime mismatch                   -> REJECT
false positive                    -> REVIEW
clean replay + headroom           -> ACCEPT
```

## 3. Historical replay packet completeness contract

Added after repository audit:

`analysis/app/orderscope_local/cross_market/historical_replay_packet.py`

The packet boundary requires repository-backed evidence over one common replay window for all canonical cross-asset input lanes:

```text
oil_price
commodity_fundamental
commodity_event
commodity_interpretation
btc_spot_etf_flow
traditional_risk
crypto_market
crypto_derivatives
volatility
```

It additionally requires expected regime / alert labels to have independent evidence IDs that are not reused as classifier-input evidence.

Synthetic evidence and non-repository-backed evidence are explicitly rejected. Missing lanes are reported rather than silently imputed.

Focused tests:

`analysis/tests/cross_market/test_historical_replay_packet.py`

## 4. Repository historical-data audit

The active branch contains genuine historical market-recovery evidence, including NVDA 1-minute local recovery/replay material used by L1-003. This is useful historical evidence for the traditional-risk lane, but it does **not** by itself provide the complete UWBS-080..085 cross-asset packet.

The audit has not established one repository-backed historical window that simultaneously supplies all nine required lanes above.

Therefore:

- existing NVDA historical recovery evidence must not be presented as complete cross-asset calibration;
- synthetic `broad-risk-on`, `crypto-only`, and `noise` fixtures remain regression fixtures only;
- no historical false-positive / false-negative rate may yet be claimed;
- final UWBS-086 acceptance remains open.

## 5. Current repository-grounded runtime capacity facts

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

Therefore a deliberately conservative statement-execution ceiling is:

```text
1,440 invocations/day * 40 D1 executions/invocation = 57,600 D1 executions/day
```

This number is **not** a D1 billing-row estimate. A query can read/write zero, one or multiple rows.

The market-bar batch path also accepts up to the configured per-job bar cap and uses set-oriented D1 statements. Consequently `D1 executions/day` cannot be substituted for either `rows_read/day` or `rows_written/day`.

## 6. Extended capacity model

The original capacity evaluator included Worker requests, D1 rows written, D1 bytes and optional scheduled-invocation headroom. Final acceptance prerequisites also require D1 rows read, so the model has been extended to include:

```text
worker_requests_per_day
d1_rows_read_per_day
d1_rows_written_per_day
d1_bytes_written_per_day
scheduled_invocations_per_day
```

`build_capacity_observation()` now computes headroom from the most constrained supplied resource including D1 read rows.

This extension requires local regression verification before it is treated as accepted software evidence.

## 7. Fresh platform planning envelope

As of 2026-09-27, the previously captured Cloudflare planning envelope was:

```text
Workers requests:       100,000/day
D1 rows read:         5,000,000/day
D1 rows written:        100,000/day
D1 maximum DB size:         500 MB
D1 account storage:           5 GB
D1 queries/Worker invocation: 50 (Free platform limit)
Cron triggers/account:         5
```

OrderScope's internal D1 statement-execution ceiling of 40/invocation is below the captured platform query limit. These platform values remain external planning evidence rather than domain constants and must be refreshed at final capacity acceptance.

## 8. Remaining capacity evidence gap

No checked-in collector currently records Cloudflare D1 billing metadata as daily `rows_read`, `rows_written`, and storage-growth evidence for this cross-asset lane.

Final capacity acceptance therefore needs one of the following defensible paths:

1. measured billing-row metadata from a bounded non-mutating/local or separately authorized canary execution; or
2. a conservative statement-by-statement row bound derived from the actual intended cross-asset storage schema and schedule.

No live Worker/Cron or remote D1 mutation is authorized by this document.

## 9. Final acceptance prerequisites

Final UWBS-086 acceptance requires at least:

1. local verification of the historical replay packet completeness contract;
2. local verification of the D1-read-aware capacity evaluator;
3. one or more repository-backed historical cross-asset replay packets with expected labels defined independently of the classifier under test;
4. replay summary with false positives, false negatives and regime mismatches;
5. measured or defensibly bounded D1 `rows_read`, `rows_written`, and storage growth for the intended schedule;
6. Worker request usage projection;
7. capacity headroom calculation against a freshly verified platform envelope;
8. final `ACCEPT / REVIEW / REJECT` decision.

## 10. Safe close

No live provider activation, Worker/Cron mutation, D1 mutation, PB execution or trading action was performed for this audit.
