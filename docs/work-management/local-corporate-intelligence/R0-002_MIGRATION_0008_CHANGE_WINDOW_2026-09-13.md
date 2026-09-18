# OrderScope — R0-002 Migration 0008 Schema-Only Change Window

Status: **READY FOR EXPLICIT EXECUTION AUTHORIZATION**
Date: 2026-09-13 JST
Branch: `docs/mermaid-conventions-v0.1`
Environment: `live-canary`
Migration: `0008_scheduler_run_evidence.sql`

## 1. Purpose

Apply only the additive scheduler-run-evidence schema to the isolated `live-canary` D1 database while leaving the runtime feature disabled.

This is a schema-only operation. It does not authorize Worker deployment, Cron mutation, News activation, `full-v0.1`, SMOKE-007, D1 export/purge, or scheduler-evidence feature activation.

## 2. Reviewed migration contents

`0008_scheduler_run_evidence.sql` contains only:

- `CREATE TABLE IF NOT EXISTS scheduler_run (...)`;
- `CREATE TABLE IF NOT EXISTS scheduler_run_job (...)`;
- `CREATE INDEX IF NOT EXISTS idx_scheduler_run_started_at ...`;
- `CREATE INDEX IF NOT EXISTS idx_scheduler_run_job_status ...`.

It has no destructive DDL or data backfill.

Runtime activation is separately gated by `SCHEDULER_RUN_EVIDENCE_ENABLED`. The checked-in live-canary config does not enable it, and runtime defaults the missing value to `false`.

## 3. Preconditions

Before execution, all must be true:

```text
branch                         = docs/mermaid-conventions-v0.1
Worker mode                    = shadow
News acquisition               = disabled
Universe                       = canary-v0.1
Cron                           = * * * * *
pending migration              = 0008_scheduler_run_evidence.sql only
SCHEDULER_RUN_EVIDENCE_ENABLED = unset/false
Cloudflare control path        = healthy
```

If any other migration appears, stop.

## 4. Read-only preflight

```bash
git checkout docs/mermaid-conventions-v0.1
git pull --ff-only origin docs/mermaid-conventions-v0.1
git status --short
git rev-parse HEAD

npx wrangler whoami
npx wrangler d1 info STATE_DB --env live-canary
npx wrangler d1 migrations list STATE_DB --remote --env live-canary
npx wrangler d1 execute STATE_DB --remote --env live-canary --command "SELECT 1 AS control_path_ok;"
npx wrangler d1 execute STATE_DB --remote --env live-canary --command "PRAGMA table_list;"
curl -fsS http://orderscope-market-worker-live-canary.yuihout2.workers.dev/health
```

Expected:

- authenticated account resolves normally;
- D1 target is `orderscope-state-live-canary`;
- only migration `0008_scheduler_run_evidence.sql` is pending;
- `SELECT 1` succeeds;
- `/health` remains Shadow and News disabled.

## 5. Explicit execution command

**Do not run this section without explicit authorization for this change window.**

```bash
npx wrangler d1 migrations apply STATE_DB --remote --env live-canary
```

No Worker deploy or config edit is part of this window.

## 6. Post-apply verification

Immediately verify:

```bash
npx wrangler d1 migrations list STATE_DB --remote --env live-canary

npx wrangler d1 execute STATE_DB --remote --env live-canary --command \
  "SELECT name FROM sqlite_schema WHERE type='table' AND name IN ('scheduler_run','scheduler_run_job') ORDER BY name;"

npx wrangler d1 execute STATE_DB --remote --env live-canary --command \
  "SELECT name FROM sqlite_schema WHERE type='index' AND name IN ('idx_scheduler_run_started_at','idx_scheduler_run_job_status') ORDER BY name;"

curl -fsS http://orderscope-market-worker-live-canary.yuihout2.workers.dev/health
```

Required result:

```text
pending migrations             = none
scheduler_run                  = exists
scheduler_run_job              = exists
idx_scheduler_run_started_at   = exists
idx_scheduler_run_job_status   = exists
Worker mode                    = shadow
News acquisition               = disabled
```

## 7. Failure handling

Stop immediately and do not enable the runtime feature if:

- Cloudflare control path returns `7403` or another authorization error;
- a migration other than `0008` is pending/applied unexpectedly;
- migration application reports partial/failure state;
- expected tables/indexes are missing;
- Worker/config state drifts from Shadow/News-disabled.

Because the migration is additive, rollback is **not** an automatic destructive DROP operation. On failure, preserve the schema state, keep the feature disabled, capture evidence, and review before any remediation.

## 8. Acceptance boundary

R0-002 remote schema window is accepted only when:

- preflight target and pending set are correct;
- `0008` applies successfully;
- no pending migration remains;
- both tables and both indexes are present;
- Worker remains Shadow;
- News remains disabled;
- scheduler evidence remains disabled;
- no unrelated remote mutation occurred.

Applying the schema does **not** authorize `SCHEDULER_RUN_EVIDENCE_ENABLED=true`.

## 9. Return record

Capture:

```text
pre-window HEAD:
D1 database:
pending migrations before:
apply result:
pending migrations after:
scheduler_run exists: yes/no
scheduler_run_job exists: yes/no
indexes exist: yes/no
final Worker mode:
final News state:
scheduler evidence enabled: no
control-path error observed: yes/no
final disposition: ACCEPTED / BLOCKED
reason:
```
