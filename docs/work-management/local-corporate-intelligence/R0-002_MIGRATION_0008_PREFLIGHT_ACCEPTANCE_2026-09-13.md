# OrderScope — R0-002 Migration 0008 Preflight Acceptance

Status: **READY FOR REMOTE APPLY AUTHORIZATION**
Date: 2026-09-13 JST
Branch: `docs/mermaid-conventions-v0.1`
Scope: `0008_scheduler_run_evidence.sql` remote D1 schema-only migration preflight for `live-canary`

## 1. Observed preflight result

The operator executed the reviewed read-only preflight against the isolated `live-canary` environment.

Observed result:

- branch synchronized through `e433f80c4e26095a11de4d5abd7b8ec8de951d0d`;
- Cloudflare OAuth identity resolved successfully;
- selected D1 database: `orderscope-state-live-canary`;
- selected D1 database ID matched the reviewed `live-canary` binding;
- only unapplied migration: `0008_scheduler_run_evidence.sql`;
- remote read-only `SELECT 1 AS control_path_ok` returned `1`;
- no existing `scheduler_run` / `scheduler_run_job` schema was reported before apply;
- deployed Worker `/health` returned `ok=true`, `mode=shadow`, News disabled;
- no `7403`, quota error, binding error, or control-path stall was observed.

No migration, Worker deployment, Cron mutation, News activation, D1 export/purge, or feature activation was performed by the preflight.

## 2. Migration review

`0008_scheduler_run_evidence.sql` is additive schema-only work:

- creates `scheduler_run` with `IF NOT EXISTS`;
- creates `scheduler_run_job` with `IF NOT EXISTS`;
- creates two indexes with `IF NOT EXISTS`;
- contains no `DROP`, `ALTER`, `DELETE`, `UPDATE`, or historical backfill.

Cloudflare Wrangler's current `d1 migrations apply` behavior applies unapplied migrations to the selected database, captures a backup, and rolls back the failing migration if it errors while preserving previously successful migrations.

## 3. Authorization boundary

The migration is now **ready for explicit remote-apply authorization**.

The approved operation, if separately authorized, is limited to:

```text
environment = live-canary
database binding = STATE_DB
migration = 0008_scheduler_run_evidence.sql
Worker deploy = no
Cron mutation = no
WORKER_MODE change = no
NEWS_ACQUISITION_ENABLED change = no
SCHEDULER_RUN_EVIDENCE_ENABLED change = no
D1 export/purge = no
```

Applying `0008` does not by itself activate scheduler run evidence. `SCHEDULER_RUN_EVIDENCE_ENABLED` must remain unset/false during this change window.

## 4. Post-apply verification

After an explicitly authorized apply, verify immediately:

1. `wrangler d1 migrations list STATE_DB --remote --env live-canary` reports no pending migration;
2. `PRAGMA table_list` contains `scheduler_run` and `scheduler_run_job`;
3. `SELECT COUNT(*)` against both new tables succeeds and returns zero rows before feature activation;
4. `/health` remains `mode=shadow` and News disabled;
5. no Worker/Cron/config mutation occurred.

If the apply fails, stop. Do not manually patch schema or enable scheduler evidence in the same window.

## 5. Disposition

```text
R0-002 local implementation        = Accepted
0008 read-only preflight           = Passed
0008 remote apply                  = Ready / explicit authorization required
scheduler evidence activation      = Still separately gated
market-day requirement             = None for schema-only apply
```
