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

For intraday equities, each provider request range must stay within one
authoritative session. If a checkpoint is exactly at a session close, the next
forward request starts at the next configured session open; it must not overlap
the prior close across the closed-session gap. Crypto remains on its continuous
`ALL_TRADING` route.

`latest bars` or snapshot endpoints may be used as an Attention fast path, but they must not replace recoverable checkpoint-based acquisition.

## 7. Environment and secrets

The Worker needs provider credentials through secret bindings rather than source-controlled configuration.

Conceptually:

```text
ALPACA_API_KEY
ALPACA_API_SECRET
```

Do not place credentials in repository Markdown, `wrangler.jsonc`, public environment variables or digest responses.

Non-secret configuration can include:

- provider route
- Universe/config revision
- overlap policy
- finalization lag
- session scopes
- cadence policy
- digest endpoint policy

### 7.1 Local CLI credential isolation

Cloudflare management credentials are not Worker bindings. Keep a management
token outside repository-local `.env` / `.dev.vars` files that Wrangler loads
when it generates Worker types. Use an authenticated Wrangler profile or a
terminal-only credential mechanism for deploy and remote-admin commands.

Before committing `worker-configuration.d.ts`, run `wrangler types --check` and
inspect the declared bindings by name. `CLOUDFLARE_API_TOKEN`, account IDs, and
other management-only values must not appear in the generated Worker `Env`
type. If they do, stop the preflight, remove the management value from the
Worker type-generation input, regenerate the type, and repeat the check. Never
record credential values in the command output, issue tracker, or this runbook.

### 7.2 Management-token recovery and least privilege

Deleting a Cloudflare management token from a local dotenv file does not revoke
the token in Cloudflare, and a token secret that is no longer retained cannot be
recovered. If the status of the removed token is unknown, revoke it in the
Cloudflare dashboard and create a replacement. Do not restore it to repository
local `.env` or `.dev.vars`.

The credential and identifier categories are:

| Item | Needed when | Storage / path |
|---|---|---|
| D1 database ID | Worker configuration and runtime | `wrangler.jsonc`; it is an identifier, not a secret. |
| Alpaca API key and secret | Live acquisition runtime | Cloudflare Worker Secrets; local development may use an ignored `.dev.vars` or `.env`. |
| Cloudflare management authentication | Dashboard/Wrangler administration only | Dashboard login, Wrangler OAuth profile, or a temporary process token outside the repository. It is not a Worker binding. |

For a one-time dedicated D1 creation, an authorized operator may create the
database in the Cloudflare dashboard and provide only its non-secret database
ID for source-controlled binding configuration. This avoids issuing a local
provisioning token.

For one-person operation, no separate executor/reviewer account, role, or
storage location is required. Record only that the user approved the specific
remote mutation and that its preflight checks passed. An approval in the Codex
client authorizes a local command; it does not authenticate that command to
Cloudflare. Cloudflare administration still requires a logged-in Dashboard or
Wrangler session, or a suitable API token.

Before using Wrangler OAuth, review the scopes shown on Cloudflare's
authorization screen. If they are broader than the intended operation, cancel
the login and use the Dashboard or a short-lived scoped API token instead.

If an API token is used, grant only the permissions needed for the operation:
`D1 Read` and `Workers Scripts Read` for inspection; `D1 Edit` for migrations;
and `Workers Scripts Write` for Secret updates and deploys. Limit it to the
intended account and a short expiry, keep it outside the repository, and remove
it from the process after use. Never place it in shell history, Worker bindings,
generated types, or an operational record.

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
  "predictions": [],
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

When the provisional Japan-to-U.S. prediction extension is enabled, each sanitized prediction entry should expose only the contract fields needed for interpretation, including target, horizon, `up_probability`, expected return, predicted volatility, distribution range, `as_of`, model/version references and quality reasons. The Worker must not train a model or fabricate a prediction from incomplete raw bars; it only publishes an already-materialized `PredictionRecord` reference/projection.

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
6. Japan-to-U.S. prediction checkpoint review after the same-day input deadline

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

### 11.1 Live Canary rollback

Use this procedure only for the explicitly named Live Canary environment. Record
the user's approval and the successful preflight checks before any Live
promotion. A separate reviewer is optional for one-person operation.

1. Stop promotion and preserve the incident time, latest digest timestamp, and
   affected coverage keys. Do not copy credential values or provider bodies.
2. Change that environment's source-controlled `WORKER_MODE` to `shadow`;
   keep `PREDICTION_MODE=shadow`. Do not remove D1 state as part of rollback.
3. Run type, test, and `wrangler deploy --dry-run --env <live-canary-env>`
   checks. Confirm that only the intended Worker and bindings are named.
4. Deploy the Shadow configuration to the same named environment, then verify
   `/health` reports `mode=shadow` and a subsequent `/digest/latest` contains
   no credential, account, or provider-response detail.
5. Record the deployment version, verifier, reason, and affected interval in
   the operational progress tracker. Keep existing D1 bars, attempts,
   checkpoints, and conflicts for diagnosis.
6. Resume Live only after the root cause, migration/binding state, Secret names,
   and a bounded Smoke test have been independently reviewed.

If D1 migration or binding consistency is in doubt, do not deploy either mode
until the remote migration list is reconciled. If provider credential exposure
is suspected, rotate the affected credential through the provider and
Cloudflare secret-management procedures before resuming acquisition.

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
