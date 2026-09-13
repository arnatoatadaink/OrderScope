# OrderScope — W1-001 Stage A Acceptance

Status: **Accepted — non-live / fixture boundary only**
Date: 2026-09-10
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`
Stage: `A — code + config + fixtures + dry-run + local acceptance`
Parent WBS revision: `docs/work-management/local-corporate-intelligence/WBS_REVISION_NEWS_WORKER_2026-09-10.md`
Implementation handoff: `docs/work-management/local-corporate-intelligence/W1-001_STAGE_A_LOCAL_HANDOFF_2026-09-10.md`

## 1. Acceptance decision

W1-001 Stage A is Accepted for the non-live / fixture boundary.

This acceptance confirms that the Worker-side News metadata acquisition path is implementable and locally testable without enabling provider access or mutating deployed infrastructure.

It does **not** authorize:

- Worker deployment;
- Cron registration/change;
- remote D1 migration/application;
- News provider activation in deployed infrastructure;
- historical catch-up;
- `WORKER_MODE=live`;
- full-Universe News expansion.

Worker remains Shadow until a separate reviewed change window explicitly authorizes Canary activation.

## 2. Measured local evidence

Operator-reported acceptance evidence:

```text
focused tests             = 15 passed
full tests                = 109 passed
typecheck                 = tsc --noEmit success
dry-run build             = success
News binding in dry-run   = false
git diff --check          = clean
News-disabled regression  = success
dry-run mutation count    = 0
body persistence scan     = clean
secret/log scan           = clean
```

These results satisfy the Stage-A acceptance boundary defined in the local handoff.

## 3. Accepted safety properties

The following properties are accepted from the measured Stage-A evidence:

1. Existing Worker behavior remains valid when News acquisition is disabled.
2. Dry-run does not mutate D1 or other runtime state.
3. Dry-run does not bind/activate live News acquisition.
4. Article body content does not cross the durable persistence boundary.
5. Provider credentials and secret/header values do not appear in persisted/logged fixture output.
6. TypeScript compilation succeeds with the News Stage-A code present.
7. The full affected TypeScript suite remains green.

## 4. Cadence decision carried forward

Initial AMD/NVDA Canary cadence remains:

```text
5 minutes during the configured U.S. observation day
```

This remains a configurable Canary initial value, not a permanent constant.

N1-006 measured provider-publication lag does not measure Worker polling delay, so live Canary must measure:

```text
provider_published_at -> worker_retrieved_at
provider_published_at -> accepted_at
scheduled_at -> run_started_at
run_started_at -> run_finished_at
```

Only those runtime measurements may support relaxing 5 minutes to 10/15 minutes later.

## 5. Remaining gate before live Canary

Stage A Accepted

```text
-> re-check current Alpaca News terms / rate limits
-> re-check current Cloudflare Worker/Cron/D1 limits relevant to the Canary
-> review prepared migration/change set and configuration
-> explicit Worker Canary change-window approval
-> AMD/NVDA live Canary only
-> collect runtime lag/call-budget/failure/retry evidence
-> decide whether 5-minute cadence remains appropriate
```

No live step is authorized by this acceptance document itself.

## 6. Stage-B acceptance target

A future live Canary acceptance must, at minimum, prove:

- only AMD/NVDA News acquisition is active;
- metadata only, no body persistence;
- bounded five-minute session-aware scheduling;
- no duplicate durable article identity across AMD/NVDA query membership;
- checkpoint advances only after completed bounded acquisition;
- retryable failures remain inspectable and do not fabricate success;
- page/article/call budget is bounded;
- credentials remain absent from D1/logs/digests;
- runtime publication-to-retrieval/acceptance latency is measured;
- existing Market Bars behavior remains unaffected;
- rollback to News-disabled/Shadow behavior is documented and tested.

## 7. Current state

```text
N1-006                 Accepted
UWBS-016                Incorporated as W1-001
W1-001 Stage A          Accepted — non-live / fixture boundary
W1-001 live Canary      Gated / not authorized
Worker mode             Shadow
remote D1 mutation      Not authorized
Cron registration       Not authorized
```
