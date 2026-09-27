#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="live-canary"
DB_BINDING="STATE_DB"
HEALTH_URL="http://orderscope-market-worker-live-canary.yuihout2.workers.dev/health"

echo "== pending migrations =="
npx wrangler d1 migrations list "$DB_BINDING" --remote --env "$ENV_NAME"

echo "== scheduler evidence schema =="
npx wrangler d1 execute "$DB_BINDING" --remote --env "$ENV_NAME" --command \
  "SELECT name, type FROM sqlite_schema WHERE name IN ('scheduler_run','scheduler_run_job','idx_scheduler_run_started_at','idx_scheduler_run_job_status') ORDER BY type, name;"

echo "== scheduler evidence row counts =="
npx wrangler d1 execute "$DB_BINDING" --remote --env "$ENV_NAME" --command \
  "SELECT 'scheduler_run' AS table_name, COUNT(*) AS row_count FROM scheduler_run UNION ALL SELECT 'scheduler_run_job', COUNT(*) FROM scheduler_run_job;"

echo "== control path =="
npx wrangler d1 execute "$DB_BINDING" --remote --env "$ENV_NAME" --command \
  "SELECT 1 AS control_path_ok;"

echo "== deployed health =="
curl -fsS "$HEALTH_URL"
echo

echo "POST-APPLY VERIFICATION COMPLETE."
echo "Expected: no pending migrations; two tables + two indexes exist; both tables have 0 rows; control_path_ok=1; Worker remains shadow with News disabled."
