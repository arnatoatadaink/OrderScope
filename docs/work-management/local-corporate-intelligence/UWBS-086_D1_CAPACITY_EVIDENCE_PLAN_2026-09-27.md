# UWBS-086 — D1 Capacity Evidence Plan — 2026-09-27

Status: **IMPLEMENTATION READY — LOCAL ACCEPTANCE REQUIRED**
Branch: `l1-003-local-market-recovery`

## Purpose

Complete the remaining UWBS-086 capacity boundary without treating D1 statement executions as billing rows.

Cloudflare D1 exposes billing-relevant query metadata including:

```text
meta.rows_read
meta.rows_written
meta.size_after
```

OrderScope will use repository-backed snapshots of those values as the preferred capacity evidence. No live D1 mutation is authorized by this plan.

## Added analyzer

`analysis/app/orderscope_local/cross_market/d1_capacity_evidence.py`

The analyzer:

1. parses billing-relevant D1 query metadata;
2. aggregates rows read/written per Worker invocation sample;
3. derives positive database storage growth when `database_size_before` and `size_after` are available;
4. selects the worst observed sample independently for reads, writes and storage growth;
5. applies an explicit safety multiplier (default 1.25x);
6. scales to scheduled invocations/day;
7. returns `ProjectedCapacityUsage` for the accepted UWBS-086 capacity evaluator.

This is deliberately more conservative than averaging samples and avoids equating query count with billed rows.

## Evidence acquisition rule

Preferred evidence order:

1. existing repository-backed D1Result meta snapshots, if available;
2. explicitly captured local/shadow invocation output that already exists;
3. a future bounded observation run only with separate authorization if no existing evidence can satisfy the acceptance boundary.

Do not mutate Worker/Cron/D1 merely to collect this evidence without explicit authorization.

## Local verification

```bash
uv run pytest -q \
  analysis/tests/cross_market/test_d1_capacity_evidence.py

uv run pytest -q \
  analysis/tests/cross_market/test_historical_canary_evaluation.py

uv run pytest -q analysis/tests

uv run python -m compileall -q analysis/app

git diff --check
```

Expected focused counts before concurrent changes:

```text
D1 capacity evidence analyzer: 10 tests
historical Canary evaluation:   7 tests
```

## Final UWBS-086 close condition

After local acceptance of this analyzer, final close still requires real repository-backed D1 metadata or a defensible non-live bound. The historical Canary side is already accepted for the 2024-08-05 packet with FP=0, FN=0 and regime mismatch=0.
