#!/usr/bin/env bash
set -euo pipefail

BRANCH="docs/mermaid-conventions-v0.1"
ENVIRONMENT="live-canary"
DB_BINDING="STATE_DB"
HEALTH_URL="http://orderscope-market-worker-live-canary.yuihout2.workers.dev/health"

printf '%s\n' '== git ==' 
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
git status --short
git rev-parse HEAD

printf '%s\n' '== Cloudflare identity / D1 target =='
npx wrangler whoami
npx wrangler d1 info "$DB_BINDING" --env "$ENVIRONMENT"

printf '%s\n' '== pending migrations =='
npx wrangler d1 migrations list "$DB_BINDING" --remote --env "$ENVIRONMENT"

printf '%s\n' '== read-only control probe =='
npx wrangler d1 execute "$DB_BINDING" --remote --env "$ENVIRONMENT" --command "SELECT 1 AS control_path_ok;"

printf '%s\n' '== existing scheduler evidence schema =='
npx wrangler d1 execute "$DB_BINDING" --remote --env "$ENVIRONMENT" --command "SELECT type, name FROM sqlite_schema WHERE name IN ('scheduler_run','scheduler_run_job','idx_scheduler_run_started_at','idx_scheduler_run_job_status') ORDER BY type, name;"

printf '%s\n' '== deployed health =='
curl -fsS "$HEALTH_URL"
printf '\n'

cat <<'EOF'

READ-ONLY R0-002 PREFLIGHT COMPLETE.

Expected before authorization:
  only pending migration = 0008_scheduler_run_evidence.sql
  Worker mode            = shadow
  News acquisition       = disabled
  control_path_ok        = 1

This script performs no migration apply, Worker deploy, Cron mutation, News activation,
D1 export/purge, or feature activation.
EOF
