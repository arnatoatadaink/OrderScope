# OrderScope v0.1 — Cloudflare Worker / Cron / ChatGPT Schedule Runbook

Status: non-normative operational runbook
Date: 2026-08-28

## 1. Purpose

This runbook describes how the current provider-neutral design can be deployed on Cloudflare Workers and how ChatGPT Scheduled Tasks should consume the resulting digest.

The deployment products are adapters. They do not redefine Core contracts.

## 2. Runtime topology

```text
Cloudflare Cron Trigger
  -> Worker scheduler adapter
  -> Session Gate
  -> SchedulePolicy
  -> AcquisitionJob
  -> AcquisitionExecutor
  -> AlpacaProviderAdapter
  -> MarketDataAcceptancePort
  -> CoverageCheckpointPort / state storage
  -> Digest Builder
  -> HTTPS digest/state endpoint

ChatGPT Scheduled Task
  -> periodically read digest/state
  -> interpret Attention / Fact changes
  -> summarize / prioritize / report
```

Market-data collection remains on the Worker side. ChatGPT Schedule is not the one-minute collector.

## 3. Cloudflare resources

Initial deployment may use:

- Workers for scheduler and acquisition execution
- Cron Triggers for wake-up
- D1 or another durable adapter for checkpoint/state/digest metadata
- R2 or another storage adapter if raw/high-density bar retention is needed
- Queue only for meaningful state/event transitions if needed

The exact storage product remains replaceable.

## 4. Worker entry points

The Worker implementation should expose two independent entry paths.

### Scheduled entry

```text
scheduled(event, env, ctx)
  -> runSchedulerTick(now)
```

Responsibilities:

1. load/cache market calendar
2. classify current market session
3. load Universe/config revision
4. load relevant coverage checkpoints
5. call `SchedulePolicy.plan(...)`
6. execute/enqueue due AcquisitionJobs
7. update lightweight digest state

### HTTP entry

Suggested endpoints:

```text
GET /health
GET /digest/latest
GET /coverage/summary
```

The digest endpoint should expose already-aggregated state, not require ChatGPT to query every symbol individually.

## 5. Cron strategy

Use a broad UTC cron and perform market-time logic in the Worker.

For the one-minute-capable design, an implementation candidate is:

```toml
[triggers]
crons = ["* * * * *"]
```

This is a deployment example, not a normative cadence requirement.

Do not encode the U.S. Regular session as a fixed UTC interval because Eastern Time DST, holidays and early closes change the valid trading grid.

Instead:

```text
Cron wake-up
  -> Session Gate using America/New_York calendar
  -> CLOSED: do nothing except optional health/calendar work
  -> PREMARKET/REGULAR/AFTER_HOURS: plan only configured jobs
```

## 6. Acquisition behaviour

The canonical acquisition path is:

```text
load checkpoint
  -> requested_start = complete_through - configured overlap
  -> requested_end = latest finalizable boundary
  -> fetch historical bars
  -> normalize
  -> idempotent accept
  -> recompute contiguous coverage
  -> compare-and-set checkpoint
```

`latest bars` or snapshot endpoints may be used as an Attention fast path, but they must not replace recoverable checkpoint-based acquisition.

## 7. Environment and secrets

The Worker needs provider credentials through secret bindings rather than source-controlled configuration.

Conceptually:

```text
ALPACA_API_KEY
ALPACA_API_SECRET
```

Do not place credentials in repository Markdown, `wrangler.toml`, public environment variables or digest responses.

Non-secret configuration can include:

- provider route
- Universe/config revision
- overlap policy
- finalization lag
- session scopes
- cadence policy
- digest endpoint policy

## 8. Digest contract

The first digest should be intentionally compact.

Suggested logical fields:

```json
{
  "generated_at": "UTC instant",
  "market_session": "PREMARKET|REGULAR|AFTER_HOURS|CLOSED",
  "universe_revision": "opaque revision",
  "coverage": {
    "expected": 0,
    "complete": 0,
    "partial": 0,
    "blocked": 0
  },
  "attention": [],
  "events": [],
  "provider_quality": {
    "feed_variant": "logical variant",
    "iex_sip_validation_pending": 0
  }
}
```

Attention entries should prefer deterministic fields such as:

- symbol/internal instrument id
- price return
- relative volume
- activity/notional proxy
- market/sector relative return
- reason codes
- evidence timestamps
- feed/data variant

ChatGPT should interpret these fields rather than reconstruct them from raw bars.

## 9. ChatGPT Scheduled Task usage

Use ChatGPT Scheduled Tasks as a lower-frequency interpretation layer.

Recommended first task:

```text
Read the latest OrderScope market digest. Compare Attention, coverage and event changes with the previous available state. Report only meaningful changes, distinguish observed Facts from Derived Metrics and interpretation, and flag coverage/provider-quality problems. If there are no meaningful changes, keep the report brief.
```

A practical schedule is hourly or at selected market checkpoints. The exact cadence should be chosen from the available Scheduled Task limits and the desired reporting latency.

Suggested logical uses, if task capacity is available:

1. Market / Attention digest
2. Earnings / event review
3. Macro / Barometer digest
4. Fact / Regime change review
5. System health / coverage review

Do not create one ChatGPT task per symbol.

## 10. Authentication boundary for the digest

The digest should not expose provider secrets or write controls.

Possible deployment patterns, to be selected later:

- public read-only digest with no sensitive data and an unguessable/non-indexed path
- authenticated read-only endpoint if the consuming environment can present credentials
- publish the digest to another supported surface consumed by the analysis workflow

The exact ChatGPT-to-private-Worker authentication method is still unresolved and must be tested before production use.

## 11. Initial deployment sequence

1. implement Worker scheduler/session gate shell
2. implement Alpaca provider adapter behind existing provider contract
3. implement checkpoint/state persistence adapter
4. implement historical overlap acquisition
5. implement idempotent OHLCV acceptance
6. add volume/activity derived fields needed by Attention
7. add `/health` and `/digest/latest`
8. deploy Worker with secrets
9. enable Cron trigger
10. observe CPU time, subrequests, storage writes and provider responses
11. validate IEX real-time vs delayed SIP historical where applicable
12. only after the endpoint is stable, create ChatGPT Scheduled Task(s) that read the digest

## 12. Verification checklist

Before enabling unattended monitoring, verify:

- duplicate Cron deliveries do not duplicate bars
- a missed Cron tick is recovered through historical catch-up
- checkpoint never advances across unresolved gaps
- holiday/weekend creates no synthetic intraday bars
- early close is respected
- DST transition does not require changing cron expression
- IEX volume is labelled as its own feed/data variant
- delayed SIP validation cannot silently overwrite conflicting observations
- provider/API failure appears in coverage/health digest
- Worker CPU and storage usage are measured rather than assumed
- ChatGPT digest interpretation remains non-critical to data collection

## 13. Current unknowns

- production storage split between D1/R2/other adapters
- exact Normal/Watch/Attention cadence
- overlap duration and finalization lag
- Attention maximum concurrency
- digest authentication approach
- exact Scheduled Task cadence
- raw bar retention
- quote/trade scope
