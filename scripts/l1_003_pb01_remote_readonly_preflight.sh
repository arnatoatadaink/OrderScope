#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"
ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"

echo "L1-003 PB-01 remote read-only preflight"
echo "environment=${ENV_NAME}"
echo "database=${DB_NAME}"
echo "coverage_key=${COVERAGE_KEY}"
echo "remoteMutation=false"
echo

echo "== wrangler identity =="
npx wrangler whoami

echo
echo "== D1 control read =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote --command "SELECT 1 AS control_pass;"

echo
echo "== NVDA checkpoint =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote --command "
SELECT
  coverage_key,
  symbol,
  interval,
  session_scope,
  logical_data_variant,
  complete_through,
  state,
  missing_ranges_json,
  source_observed_through,
  universe_revision,
  version,
  blocker_json,
  retry_not_before
FROM coverage_checkpoint
WHERE coverage_key = '${COVERAGE_KEY}';
"

echo
echo "== unresolved attempts for NVDA =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote --command "
SELECT
  COUNT(*) AS unresolved_attempts,
  MIN(started_at) AS oldest_started_at
FROM acquisition_attempt
WHERE coverage_key = '${COVERAGE_KEY}'
  AND finished_at IS NULL
  AND outcome IS NULL;
"

echo
echo "PB-01 remote read-only preflight commands completed; no mutation statements were issued."
