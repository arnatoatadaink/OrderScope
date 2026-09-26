#!/usr/bin/env bash
set -euo pipefail
# Read-only only: no deploy, scheduled invocation, secret or D1 mutation.
[[ "$(git branch --show-current)" == l1-003-local-market-recovery ]] || exit 1
OUTPUT="$(mktemp -d /tmp/orderscope-pb09-preparation.XXXXXX)"
export WRANGLER_LOG_PATH="${OUTPUT}/wrangler.log"
git rev-parse HEAD > "${OUTPUT}/release.txt"
git status --short > "${OUTPUT}/worktree.txt"
node --input-type=module - <<'NODE'
import fs from 'node:fs';
const text=fs.readFileSync('wrangler.jsonc','utf8');
if((text.match(/"ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES": "1"/g)??[]).length!==2)throw new Error('refreeze finalization lag');
if((text.match(/"WORKER_MODE": "shadow"/g)??[]).length!==2)throw new Error('checked-in baseline changed');
NODE
npx wrangler whoami > "${OUTPUT}/identity.txt"
CLOUDFLARE_ENV=live-canary bash scripts/run-wrangler-with-env.sh d1 info orderscope-state-live-canary > "${OUTPUT}/database.txt"
rg -q '03c85865-1aa3-4b0c-b219-18987cd260a6' "${OUTPUT}/database.txt" || { echo 'D1 identity mismatch' >&2; exit 1; }
curl -fsS https://orderscope-market-worker-live-canary.yuihout2.workers.dev/health > "${OUTPUT}/health.json"
for endpoint in historical-recovery/nvda/local-evidence-next-chunk pb08/reproducible-absence/ack; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST "https://orderscope-market-worker-live-canary.yuihout2.workers.dev/control/${endpoint}")"
  [[ "${code}" == 404 ]] || { echo 'temporary control gate open' >&2; exit 1; }
done
CLOUDFLARE_ENV=live-canary bash scripts/run-wrangler-with-env.sh d1 execute orderscope-state-live-canary --remote --json --command 'SELECT coverage_key,version,complete_through,source_observed_through,state,missing_ranges_json,blocker_json,retry_not_before FROM coverage_checkpoint WHERE coverage_key IN ("AMD|1Min|REGULAR|stock:iex:raw","NVDA|1Min|REGULAR|stock:iex:raw","QQQ|1Min|REGULAR|stock:iex:raw","SPY|1Min|REGULAR|stock:iex:raw","BTCUSD|1Min|ALL_TRADING|crypto:us") ORDER BY coverage_key; SELECT COUNT(*) AS unresolved_canary_attempts FROM acquisition_attempt WHERE coverage_key IN ("AMD|1Min|REGULAR|stock:iex:raw","NVDA|1Min|REGULAR|stock:iex:raw","QQQ|1Min|REGULAR|stock:iex:raw","SPY|1Min|REGULAR|stock:iex:raw","BTCUSD|1Min|ALL_TRADING|crypto:us") AND finished_at IS NULL AND outcome IS NULL; SELECT 1 AS control_path_ok; SELECT generated_at,payload_json FROM latest_digest WHERE digest_key="market";' > "${OUTPUT}/state.json"
CLOUDFLARE_ENV=live-canary bash scripts/run-wrangler-with-env.sh deployments list --json > "${OUTPUT}/deployments.json"
node --env-file=.env --experimental-strip-types scripts/l1_003_pb09_prepare.ts "${OUTPUT}"
echo "read-only preparation artifacts: ${OUTPUT}"
echo 'remoteMutation=false; Phase B not authorized'
