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

echo "== PB-07 entry reconciliation (read-only) =="
echo "remoteMutation=false"
echo "observed_now=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
echo

echo "== deployed baseline =="
health="$(curl -fsS "${BASE_URL%/}/health")"
echo "${health}"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2)); throw new Error("unsafe baseline");
}
NODE

echo
echo "== current NVDA checkpoint =="
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
echo "== NVDA attempts since PB-07 preflight =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT started_at, finished_at, outcome, job_id, diagnostic_json
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND started_at >= '2026-09-24T11:28:48.000Z'
ORDER BY started_at ASC;
"

echo
echo "== market digests since PB-07 preflight =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT generated_at,
       json_extract(payload_json,'$.mode') AS mode,
       json_extract(payload_json,'$.status') AS status,
       json_extract(payload_json,'$.jobPlans') AS job_plans,
       json_extract(payload_json,'$.summaries') AS summaries,
       json_extract(payload_json,'$.budget.withinBudget') AS within_budget
FROM digest_history
WHERE digest_key='market'
  AND generated_at >= '2026-09-24T11:28:48.000Z'
ORDER BY generated_at ASC
LIMIT 100;
" || true

echo
echo "== latest digest =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT digest_key, generated_at, payload_json
FROM latest_digest
WHERE digest_key='market'
LIMIT 1;
"

echo
echo "PB-07 entry reconciliation complete; no mutation performed."
