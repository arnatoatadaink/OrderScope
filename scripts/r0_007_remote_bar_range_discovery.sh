#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT="live-canary"
DATABASE="STATE_DB"

printf '%s\n' '== D1 target =='
npx wrangler d1 info orderscope-state-live-canary --env "$ENVIRONMENT"

printf '%s\n' '== normalized_bar global range =='
npx wrangler d1 execute "$DATABASE" \
  --env "$ENVIRONMENT" \
  --remote \
  --command "SELECT COUNT(*) AS row_count, MIN(bar_start_utc) AS first_bar_start_utc, MAX(bar_start_utc) AS last_bar_start_utc FROM normalized_bar"

printf '%s\n' '== normalized_bar daily distribution =='
npx wrangler d1 execute "$DATABASE" \
  --env "$ENVIRONMENT" \
  --remote \
  --command "SELECT substr(bar_start_utc,1,10) AS utc_day, COUNT(*) AS row_count, MIN(bar_start_utc) AS first_bar_start_utc, MAX(bar_start_utc) AS last_bar_start_utc FROM normalized_bar GROUP BY substr(bar_start_utc,1,10) ORDER BY utc_day DESC LIMIT 14"

printf '%s\n' '== control path =='
npx wrangler d1 execute "$DATABASE" \
  --env "$ENVIRONMENT" \
  --remote \
  --command "SELECT 1 AS control_path_ok"

cat <<'EOF'
READ-ONLY R0-007 RANGE DISCOVERY COMPLETE.

No row export, Worker mutation, D1 write, purge, migration, or feature activation is performed.
Use the smallest historical non-empty interval as the next bounded custody-transfer candidate.
EOF
