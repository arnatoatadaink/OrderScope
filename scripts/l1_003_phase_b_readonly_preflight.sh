#!/usr/bin/env bash
# L1-003 / SMOKE-007 Phase B market-session preflight.
#
# This script is deliberately read-only.  It does not invoke a Worker route
# that schedules work, deploy a Worker, modify Cron, or issue any D1 write.
set -euo pipefail

ENVIRONMENT="live-canary"
DATABASE="STATE_DB"
HEALTH_URL="https://orderscope-market-worker-live-canary.yuihout2.workers.dev/health"
# The managed execution environment does not permit writes below the default
# Wrangler config directory. Keep diagnostic logs ephemeral and out of Git.
export WRANGLER_LOG_PATH="${WRANGLER_LOG_PATH:-/tmp/l1-003-phase-b-wrangler.log}"

# The operator-maintained Cloudflare credentials may be stored with CRLF line
# endings. Load them only when the caller has not supplied a token, normalizing
# line endings in-process so no secret is copied to disk or echoed.
if [[ -z "${CLOUDFLARE_API_TOKEN:-}" && -f .env.cloudflare ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(tr -d '\r' < .env.cloudflare)
  set +a
fi

printf '%s\n' '== release / worktree =='
git status --short
git rev-parse HEAD

printf '%s\n' '== Cloudflare identity and D1 target =='
npx wrangler whoami
npx wrangler d1 info "$DATABASE" --env "$ENVIRONMENT"

printf '%s\n' '== deployed health (must remain shadow; News disabled) =='
curl --fail --silent --show-error "$HEALTH_URL"
printf '\n'

printf '%s\n' '== read-only control path =='
npx wrangler d1 execute "$DATABASE" --remote --env "$ENVIRONMENT" \
  --command 'SELECT 1 AS control_path_ok;'

printf '%s\n' '== Market checkpoint candidates =='
npx wrangler d1 execute "$DATABASE" --remote --env "$ENVIRONMENT" \
  --command "SELECT coverage_key, symbol, interval, session_scope, logical_data_variant, complete_through, state, missing_ranges_json, last_success_at, last_attempt_at, source_observed_through, version FROM coverage_checkpoint WHERE session_scope = 'REGULAR' ORDER BY CASE state WHEN 'COMPLETE' THEN 0 WHEN 'UNKNOWN' THEN 1 WHEN 'PARTIAL' THEN 2 WHEN 'BLOCKED' THEN 3 ELSE 4 END, complete_through DESC, coverage_key;"

printf '%s\n' '== unresolved Market checkpoint evidence =='
npx wrangler d1 execute "$DATABASE" --remote --env "$ENVIRONMENT" \
  --command "SELECT coverage_key, state, complete_through, missing_ranges_json, blocker_json FROM coverage_checkpoint WHERE session_scope = 'REGULAR' AND (state <> 'COMPLETE' OR missing_ranges_json <> '[]' OR blocker_json IS NOT NULL) ORDER BY coverage_key;"

printf '%s\n' '== most recent scheduler digest =='
npx wrangler d1 execute "$DATABASE" --remote --env "$ENVIRONMENT" \
  --command "SELECT digest_key, generated_at, payload_json FROM latest_digest ORDER BY generated_at DESC LIMIT 1;"

printf '%s\n' '== recent Market acquisition outcomes =='
npx wrangler d1 execute "$DATABASE" --remote --env "$ENVIRONMENT" \
  --command "SELECT coverage_key, started_at, finished_at, outcome FROM acquisition_attempt WHERE coverage_key IN (SELECT coverage_key FROM coverage_checkpoint WHERE session_scope = 'REGULAR') ORDER BY started_at DESC LIMIT 30;"

cat <<'EOF'

READ-ONLY L1-003 / SMOKE-007 PHASE B PREFLIGHT COMPLETE.

Review the output against the candidate-selection rule in
docs/work-management/local-corporate-intelligence/
L1-003_SMOKE-007_PHASE_B_CLOSED_MARKET_PREP_2026-09-15.md.

Do not activate Phase B from this script.  A separate explicit authorization
for the bounded pause/resume window remains required.  If no current COMPLETE
Market checkpoint has an unambiguous session boundary, record
"market-day evidence unavailable" and do not widen scope.
EOF
