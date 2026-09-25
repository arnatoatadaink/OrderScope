#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"

fail() { echo "ERROR: $*" >&2; exit 1; }

[[ "${ENV_NAME}" == "live-canary" ]] || fail "CLOUDFLARE_ENV must be live-canary"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || fail "wrong branch"
git diff --quiet || fail "worktree has unstaged changes"
git diff --cached --quiet || fail "worktree has staged changes"

echo "== PB-08 fresh remote catch-up preflight (read-only) =="
echo "remoteMutation=false"
echo "observed_now=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
echo "git_commit=$(git rev-parse HEAD)"
echo

health="$(curl -fsS "${BASE_URL%/}/health")"
echo "== deployed baseline =="
echo "${health}"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2)); throw new Error("unsafe baseline");
}
NODE

code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${code}" == "404" ]] || fail "historical recovery endpoint must be closed"

echo
echo "== exact current checkpoint / unresolved attempts =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before,
       universe_revision
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}';

SELECT COUNT(*) AS unresolved_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND finished_at IS NULL AND outcome IS NULL;
"

echo
echo "== fresh canary competition snapshot =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint
WHERE coverage_key IN (
  'SPY|1Min|REGULAR|stock:iex:raw',
  'QQQ|1Min|REGULAR|stock:iex:raw',
  'NVDA|1Min|REGULAR|stock:iex:raw',
  'AMD|1Min|REGULAR|stock:iex:raw',
  'BTCUSD|1Min|ALL_TRADING|crypto:us'
)
ORDER BY coverage_key;
"

echo
echo "== recent NVDA attempts =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT started_at, finished_at, outcome, job_id, diagnostic_json
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
ORDER BY started_at DESC LIMIT 8;

SELECT digest_key, generated_at, payload_json
FROM latest_digest
WHERE digest_key='market'
LIMIT 1;
"

echo
echo "PB-08 fresh remote preflight complete."
echo "Use this snapshot only to re-freeze the bounded normal-scheduler catch-up window."
echo "No remote mutation or Phase B pause/resume is authorized."
