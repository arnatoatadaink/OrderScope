# OrderScope — W1-001 Short Confirmation / Closeout Local Handoff

Status: **Ready for separately authorized short live-canary window**
Date: 2026-09-11 JST
Task: `W1-001 — Final short confirmation/closeout after W1-007 control-path restoration`

Depends on:
- W1-006 cadence repair Accepted and live-confirmed;
- W1-001 reopen window collected 12 distinct successful eligible News buckets;
- W1-007 Accepted — control path restored.

## 1. Purpose

Do not repeat the full one-hour Canary unless new evidence requires it.

This short window exists only to prove end-to-end operational control after the recovered Cloudflare API `7403` incident:

```text
pre-activation read-only control path healthy
-> activate reviewed AMD/NVDA metadata-only Canary
-> observe a small number of eligible News buckets
-> perform read-only control-path checks while active
-> disable News / return Worker to shadow
-> verify post-rollback control path and zero News calls/mutations
```

The prior 12-bucket runtime evidence remains part of the acceptance basis.

## 2. Fixed scope

```text
environment: live-canary
Universe: canary-v0.1
News symbols: AMD,NVDA
News: metadata only
News cadence: 5 minutes
Cron: * * * * *
combined external ceiling: 40
combined D1 ceiling: 40
```

Do not change cadence, Cron, Universe, provider limits, page limits, budgets, schema, or News symbols during this window.

## 3. Pre-window control-path check

Before activation, run and record two successful read-only checks if practical:

```bash
npx wrangler whoami
npx wrangler d1 info orderscope-state-live-canary --env live-canary
npx wrangler d1 execute orderscope-state-live-canary --env live-canary --remote --command="SELECT 1 AS control_path_ok;"
```

Confirm:

```text
Worker mode = shadow
News enabled = false
Universe = canary-v0.1
Cron = * * * * *
rollback/safe deployment is healthy
```

If `7403`, account mismatch, auth loss, or a command stall recurs, do not activate.

## 4. Activation

Inside an operator-monitored change window, activate only the reviewed pair:

```text
WORKER_MODE=live
NEWS_ACQUISITION_ENABLED=true
```

Keep all other variables unchanged.

Record activation version and UTC/JST timestamp.

## 5. Minimum live confirmation

Observe **at least 3 distinct eligible five-minute News buckets**.

For each, record:

```text
scheduled timestamp
News planned/selected/completed/failed
Market outcome
external total / 40
D1 total / 40
withinBudget
article observation count if any
CPU/resource/exception indicators
```

Acceptance target:

```text
3 distinct eligible buckets
News completed on each eligible bucket
no Market regression
external <= 40
D1 <= 40
no exceeded-resource/exception
```

No article arrival is required for this confirmation window because article correctness/lag evidence was already collected in the prior 12-bucket window.

## 6. In-window control-path proof

While the Canary is active, perform at least one bounded read-only control-path check:

```bash
npx wrangler d1 execute orderscope-state-live-canary --env live-canary --remote --command="SELECT 1 AS active_window_control_path_ok;"
```

Optionally inspect schema-only/read-only metadata if needed. Do not introduce a broad D1 scan.

If `7403`, authorization loss, or a material stall recurs, rollback immediately and return `ROLLED_BACK / Blocked`.

## 7. Controlled closeout

After the minimum 3 eligible buckets pass:

1. set `NEWS_ACQUISITION_ENABLED=false`;
2. verify the next invocation has zero News provider calls/mutations;
3. set `WORKER_MODE=shadow`;
4. record rollback/safe deployment version;
5. verify `/health` reports shadow / News disabled;
6. repeat:

```bash
npx wrangler d1 execute orderscope-state-live-canary --env live-canary --remote --command="SELECT 1 AS post_closeout_control_path_ok;"
```

The goal is to demonstrate that monitoring/control remains available through the entire closeout, not merely before activation.

## 8. Hard stop

Rollback immediately if any of the following occurs:

- Cloudflare API `7403` or equivalent auth/control loss;
- control-path command materially stalls;
- combined external > 40 or D1 > 40;
- fail-before-crossing behavior fails;
- Market regression;
- Worker exceeded-resource/CPU failure;
- unexpected News symbol expansion;
- News body/secret/auth-header leakage;
- new technical/config delta is required to continue.

Do not improvise a fix inside the live window.

## 9. Return report

Return:

```text
pre-window version:
activation version:
closeout/rollback version:
window UTC/JST:
pre-window control-path checks: pass/fail
eligible buckets observed:
News jobs planned/completed/failed:
max external/tick:
max D1/tick:
Market regression: yes/no
CPU/resource failure: yes/no
in-window SELECT 1: pass/fail
post-closeout SELECT 1: pass/fail
post-closeout News calls/mutations: 0/0 expected
final Worker mode:
final News enabled:
final disposition: ACCEPTED | ROLLED_BACK | BLOCKED | INCONCLUSIVE
reason:
```

## 10. Final decision rule

A result may be returned as `ACCEPTED — confirmation/closeout passed` if:

- at least 3 distinct eligible News buckets succeed;
- budgets remain within 40/40;
- Market remains healthy;
- read-only Cloudflare control path works before, during, and after activation;
- controlled closeout succeeds;
- final remote state is shadow + News disabled;
- no new technical delta is required.

This short confirmation does not authorize `full-v0.1`. It supplies the final missing operational-control evidence for Web review of W1-001 live acceptance.
