# Worker v0.1 — Implementation Decisions from Functional Requirements

Status: provisional, non-normative implementation decisions
Date: 2026-08-29

This document narrows unresolved implementation choices using the fixed v0.1 functional requirements. It does not modify the four-document Code of Truth.

## 1. D1 / R2 responsibility

Decision:

- **D1** stores operational state: coverage checkpoints, latest accepted state needed by the scheduler, compact derived-feature state, latest digest metadata, and reconciliation/status records.
- **R2** stores long-lived/batched OHLCV archive objects and later bulk-analysis handoff artifacts.
- The Worker must not require R2 to run the scheduler. R2 is an archive/handoff boundary; D1 is the online operational state boundary.

Reasoning:

- v0.1 requires approximately 100 instruments with 1m / 15m / 1d cadences, recovery checkpoints and time-series reconstruction.
- D1 is convenient for small keyed state and compare/update operations, but the Free database size is finite and high-density bars accumulate continuously.
- R2 is better suited to append/batch object storage and bulk transfer to the Main PC.

Illustrative regular-session bar count from the current Universe (not a measured production value):

- Tier A: 25 instruments × 390 one-minute bars ≈ 9,750 bars/trading day.
- Tier B: 24 instruments × 26 fifteen-minute bars ≈ 624 bars/trading day.
- Tier C: roughly one bar per enabled daily instrument after session finality.

This is enough to justify separating hot operational state from long-term bar retention before production measurements exist.

## 2. Acquisition cadence vs Watch / Attention

Decision:

The normative acquisition cadence remains:

- Tier A = 1 minute,
- Tier B = 15 minutes,
- Tier C = daily.

`Watch` and `Attention` are analysis/prioritization states, not independent baseline polling cadences.

Temporary cadence promotion is allowed only as an explicit policy transition with:

- reason/evidence,
- start time,
- expiry/end condition,
- target cadence,
- provenance.

For earnings/event preparation, the preferred rule is to create Attention state from one day before the scheduled event, while retaining the instrument's configured base cadence unless an explicit promotion rule applies.

This prevents duplicated scheduler semantics and preserves reproducibility.

## 3. Relative-volume baseline

Decision:

Use a **20 comparable trading-day median baseline** for the first implementation.

For intraday bars, comparison must use the same instrument, interval, session kind and aligned session-time bucket. Regular, Premarket and After-hours remain separate. Shortened sessions must not contaminate normal-session buckets.

```text
RVOL_20_MEDIAN = current_volume / median(previous 20 comparable bucket volumes)
```

Fallback hierarchy:

1. 20 comparable trading days,
2. 7 comparable trading days with quality flag `WARMING_UP`,
3. otherwise `UNAVAILABLE`.

Rationale: 20 trading days already exists as a v0.1 analysis window and median is less sensitive than a mean to event-volume spikes.

## 4. Notional activity representative price

Decision:

Use:

1. provider-neutral bar VWAP when present and accepted,
2. otherwise typical price `(high + low + close) / 3`.

```text
notional_activity_proxy = representative_price * volume
```

This remains a traded-notional/activity proxy, never a net-capital-inflow Fact.

The representative-price method and version must be stored with the derived metric.

## 5. Digest access for ChatGPT Scheduled Tasks

Decision for v0.1:

Expose a **sanitized, read-only digest endpoint** that contains no credentials, account data, private identifiers or write capability.

The public digest may contain only market Facts, Derived Metrics, coverage health and non-sensitive system status. API keys and internal diagnostics must never appear in it.

Reasoning: direct custom authenticated-header support from a Scheduled Task is not treated as a guaranteed platform capability. A sanitized read-only endpoint avoids coupling acquisition correctness to ChatGPT authentication behavior.

If the digest itself later becomes sensitive, replace this with a connector/service-account access path; do not put a long-lived secret in a Scheduled Task prompt or query string.

## 6. IEX vs SIP quality gate

Decision:

Do not invent a fixed volume-difference tolerance before observing the initial Universe.

Use delayed/full SIP historical data as the reference and measure whether IEX changes downstream decisions. The first quality report must include at least:

- per-symbol volume ratio distribution,
- RVOL rank correlation,
- Attention top-K overlap,
- false promotion/demotion cases,
- session-specific differences.

The upgrade decision should be based on decision stability, not on raw volume equality. A numeric production threshold is deferred until at least 20 comparable trading days are available.

## 7. Volatility model

Decision:

Separate Worker metrics from predictive modelling.

Worker v0.1 computes deterministic, inexpensive features only:

- log/absolute return,
- high-low range,
- realized short-window volatility,
- RVOL,
- notional activity proxy,
- gap,
- close location,
- market/sector relative return where inputs exist.

The Main PC owns the first predictive baseline. Preferred first candidate is an interpretable HAR-style realized-volatility regression aligned to the existing 1 / 7 / 20 trading-day windows, extended with RVOL/notional-activity features only after an unextended baseline is measured.

Reasoning:

- the Code of Truth says price prediction is not the primary purpose,
- heavy analysis belongs on the Main PC under `DD-DEPLOY-001`,
- a transparent baseline is needed before selecting a more complex model.

Model accuracy targets remain unresolved until a target horizon and evaluation dataset are fixed.

## 8. Worker execution mode

Decision:

The initial Worker is deployed in `shadow` mode.

Shadow mode:

- Cron Trigger runs every minute,
- `/health` and `/digest/latest` work,
- no Alpaca writes/acquisition are performed,
- missing calendar/storage/credentials are visible,
- weekday or fixed-UTC market-session guesses are forbidden.

Promotion to `live` requires:

- Alpaca secrets,
- D1 state binding,
- authoritative calendar/session implementation,
- versioned Universe loader,
- historical-bars acquisition with pagination/overlap,
- idempotent acceptance and checkpoint tests.

R2 is recommended before sustained retention but is not a blocker for the first live acquisition test.

## 9. Next implementation slice

Implement in this order:

1. Universe loader for the fixed Tier A/B/C configuration.
2. Market calendar/session port.
3. D1 schema for checkpoints + digest state.
4. Alpaca historical multi-symbol bars adapter.
5. overlap/pagination and idempotent acceptance.
6. RVOL/notional deterministic feature computation.
7. R2 batch archive writer.
8. 20-trading-day IEX vs SIP quality report.
9. Main-PC volatility baseline.
