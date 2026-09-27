# OrderScope — W1-001 Stage B Final Web Acceptance

Status: **Accepted — local/non-live preflight only**
Date: 2026-09-11
Task: `W1-001 — Implement Worker/Schedule News metadata acquisition job`

## 1. Decision

W1-001 Stage B is accepted for the reviewed local/non-live preflight boundary.

This acceptance incorporates the remediation chain:

- W1-002 — Market Bar D1 batching: Accepted;
- W1-003 — bulk checkpoint reads and shared D1 budget instrumentation: Accepted;
- W1-004 — original one-job tiered-capacity run: Blocked, with blocker superseded by W1-005;
- W1-005 — multi-symbol tier scheduler: Accepted.

No live activation is authorized by this document.

## 2. Stage-B design-freeze conditions

The original Stage-B Web freeze required:

- combined external subrequests <= 40 per scheduled invocation;
- combined D1 queries <= 40 per scheduled invocation;
- AMD/NVDA News metadata only;
- News cadence 5 minutes, configurable/provisional;
- maxPagesPerSymbol = 2;
- provider page limit <= 50;
- max raw article observations/run = 200;
- page-cap / 429 / 500 / invalid-token paths fail closed without false checkpoint advancement;
- provider article identity remains canonical while query-symbol memberships are preserved;
- News-disabled behavior restores Market-only operation;
- dry-run/shadow does not mutate acquisition state;
- no News body persistence;
- no credential/log leakage;
- no remote/live operation required.

The accepted local implementation chain satisfies these preflight conditions.

## 3. Capacity and budget evidence

Latest accepted local evidence:

```text
authoritative Universe                 25 / 28 / 53 = 106
Market checkpoint bootstrap            106 keys -> 1 D1 query
Prediction checkpoint bootstrap        bulk path retained
100-bar Market persistence             7 D1 statements
selected Market batch groups/tick      max 2
normal Tier A max backlog age          3 minutes
normal Tier B max backlog age          17 minutes
outstanding 1Min at close+30m          0
outstanding 15Min at close+30m         0
outstanding 1Day at reviewed deadline  0
normal-day NEW bars                    11,581
shortened-day NEW bars                 6,925
reviewed combined external ceiling     <= 40
reviewed combined D1 ceiling           <= 40
fail-before-crossing behavior          retained
```

Earlier reviewed combined fixture after W1-003 measured 22 D1 queries and 3 external subrequests for one Market + one News invocation. W1-005 replaces one-symbol Market execution with compatible multi-symbol batches and keeps the same shared ceilings.

## 4. News correctness evidence retained

The Stage-B News path retains the reviewed properties from Stage A/B implementation and repair work:

- metadata-only Alpaca News acquisition;
- `include_content=false`;
- provider article ID as durable identity;
- AMD/NVDA query membership preserved independently of provider symbol metadata;
- newer provider update may produce UPDATED;
- content difference without a valid newer-update basis produces CONFLICT and does not overwrite canonical content;
- page-cap continuation remains partial/retryable;
- 429 uses bounded Retry-After handling;
- 5xx remains retryable;
- invalid/looping page token fails closed;
- checkpoint completion requires proven complete bounded traversal;
- News-disabled path issues no News provider calls or News acquisition mutations;
- body and secret/log regression scans remain clean in the accepted chain.

## 5. Verification chain

Accepted evidence across the remediation chain includes:

```text
W1-002: Market 100-bar persistence = 7 statements; local fixture accepted
W1-003: focused 18/18; full 120/120; typecheck/dry-run/diff pass
W1-004: capacity blocker reproduced and documented
W1-005: focused orchestration 33 passed; full 124 passed;
        typecheck passed; Wrangler dry-run/build passed; git diff --check passed
```

No remote D1 mutation, Worker deployment, Cron change, or Worker-mode change was performed.

## 6. What this acceptance does NOT prove

The following remain live-Canary evidence and are intentionally not claimed by local acceptance:

- Cloudflare production CPU consumption;
- actual Cron scheduler delay/jitter;
- real Alpaca paging distribution and burst behavior;
- real provider-published -> Worker-retrieved/accepted News lag;
- real D1 rows/day under production traffic and retry distribution;
- full-v0.1 live Market acquisition;
- News live activation.

The five-minute News cadence remains provisional until runtime evidence is collected.

## 7. Critical-path transition

```text
W1-001 Stage A Accepted
  -> Stage B design freeze
  -> W1-002 Accepted
  -> W1-003 Accepted
  -> W1-004 blocker found
  -> W1-005 Accepted / W1-004 blocker resolved
  -> W1-001 Stage B Accepted (this document)
  -> explicit Live Canary change-window design/review
  -> user approval
  -> AMD/NVDA metadata-only News Canary
  -> runtime CPU / D1 / external / scheduler / lag evidence
```

## 8. Next authorized work

The next Web/Local work may prepare a **non-executing Live Canary change-window runbook** and acceptance checklist.

That preparation may define:

- exact Canary scope and configuration delta;
- migration/config preconditions;
- pre-flight and rollback commands;
- runtime counters and stop thresholds;
- observation duration and evidence capture;
- independent News-disable rollback;
- conditions for reverting Worker mode/config.

It must not itself deploy, mutate remote D1, change Cron, change Worker mode, enable News live, or start full-v0.1 live acquisition.

Any such live operation still requires an explicit reviewed change window and user approval.
