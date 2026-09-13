# OrderScope — W1-001 Stage B Tiered Universe Budget Revision

Status: **Active design correction — no live activation authorized**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Reference authority: `stock_monitoring_v0.1_universe_spec.md`
Current implementation reference: `src/universe.ts`

## 1. Correction

The Stage-B daily D1 write analysis must not assume that all 105 instruments are continuously acquired as 1-minute bars.

The v0.1 Universe specification explicitly separates Universe membership from price-acquisition cadence and defines:

```text
Tier A — 1 minute
Tier B — 15 minute
Tier C — Daily
```

The current `src/universe.ts` implementation already follows this model:

```text
Tier A = 25 instruments
Tier B = 28 instruments
Tier C = 53 instruments
Total  = 106 instruments
```

Therefore any `106 symbols × 390 one-minute bars/day` budget model is invalid for the current full-v0.1 normal operating model.

## 2. Current full-v0.1 distribution

### Tier A — 1Min — 25

```text
SPY QQQ IWM RSP
XLK XLF XLE XLI XLU
NVDA AMD AVGO CBRS
VRT ANET CEG VST
MSFT GOOGL AMZN META
MSTR RIOT COIN BTCUSD
```

24 are US-equity routes and BTCUSD is the crypto route.

### Tier B — 15Min — 28

```text
XLC XLY XLP XLV XLB XLRE
MRVL INTC TSM ASML AMAT LRCX KLAC MU ARM
ENTG Q MKSI MTRN
ETN PWR GEV NEE
MARA CLSK CORZ IREN CIFR
```

All 28 are US-equity routes.

### Tier C — 1Day — 53

Country proxy, macro/cross-asset, software, storage, financial, industrial, defense, energy/materials, consumer and healthcare instruments. ETHUSD is the crypto route; the remaining 52 are stock/ETF routes.

## 3. First-order normal-day bar-volume model

Use this only as a planning baseline. Local Stage-B tests must derive actual counts from scheduler fixtures, session calendars and checkpoint state.

For a normal US equity regular session of 390 minutes:

```text
Tier A equities: 24 × 390 = 9,360 bars/day
Tier A BTCUSD:    1 × 1,440 = 1,440 bars/day, if the 1Min crypto route covers a full UTC day
Tier B equities: 28 × 26 = 728 bars/day
Tier C:           53 × 1 = 53 bars/day
-------------------------------------------------
first-order total ≈ 11,581 bars/day
```

This is materially different from the invalid all-106-at-1Min model:

```text
106 × 390 = 41,340 bars/day
```

Shortened equity sessions and actual crypto scheduling/checkpoint boundaries change the exact total.

## 4. D1 row-write projection boundary

Observed W1-002 fixture evidence:

```text
100 new bars                  -> 300 row writes equivalent
same-receipt replay           -> 0 row writes
100 same bars/new receipts    -> 200 row writes equivalent
```

A naive first-order application of 3 writes/new bar to 11,581 bars gives:

```text
~34,743 Market row writes/day before overlap, retry, checkpoint, lease, attempt, digest and News writes
```

This is not an acceptance metric. It is only a baseline showing that the tiered Universe is potentially compatible with the D1 Free daily-write envelope whereas an all-105-at-1Min model is not.

The dominant uncertainty is duplicate/replay write amplification caused by overlap, retry and new acceptance receipts. Stage-B must therefore measure:

```text
new-bar writes
matched/new-receipt writes
overlap-induced repeated observations
retry-induced repeated observations
checkpoint writes
attempt writes
lease writes
digest writes
News article/membership/checkpoint writes
```

## 5. Cadence semantics

Do not conflate:

```text
bar data cadence/granularity
```

with:

```text
scheduler polling latency
```

The Universe specification defines the price-data cadence (`1Min`, `15Min`, `1Day`). The current Worker has `ACQUISITION_MAX_JOBS_PER_TICK=1`, so full-v0.1 scheduling may retrieve historical ranges in bounded catch-up jobs rather than issue one request per symbol every minute.

Stage-B must therefore test both:

1. whether the requested bar granularity is eventually complete; and
2. whether the scheduler can meet any intended freshness/latency objective.

Do not infer a one-minute end-to-end freshness SLA merely from Tier A being `1Min`.

## 6. Revised Stage-B budget model

Replace the previous homogeneous 100-bar-centric daily projection with a tier-aware workload model.

Required fixture profiles:

```text
TIER_A_NORMAL_DAY
TIER_B_NORMAL_DAY
TIER_C_NORMAL_DAY
MIXED_FULL_V01_NORMAL_DAY
SHORTENED_SESSION_DAY
OVERLAP_STEADY_STATE
MISSED_TICK_RECOVERY
PROVIDER_RETRY
NEWS_AND_MARKET_SAME_TICK
```

The existing 100-bar fixture remains useful for persistence-shape stress testing, but it is not a model of the entire 105-instrument daily workload.

## 7. Stage-B acceptance additions

Before W1-001 Stage B can be Accepted, Local must report for `full-v0.1`:

```text
instrument counts by cadence
planned bars/day by cadence
accepted NEW bars/day
MATCHED observations/day
overlap observations/day
Market row writes/day
News row writes/day
other Worker row writes/day
total projected D1 row writes/day
peak D1 queries/scheduled invocation
peak external subrequests/scheduled invocation
worst scheduler backlog age by cadence
```

Preserve the existing per-invocation ceilings and rollback requirements.

## 8. No live authorization

This correction does not authorize:

- changing `UNIVERSE_PROFILE` to full-v0.1 in a deployed Worker;
- applying remote D1 migrations;
- enabling News live;
- changing Cron;
- changing Worker Shadow mode;
- historical catch-up against remote D1.

It only corrects the Stage-B capacity model to use the already-defined v0.1 Tier allocation.
