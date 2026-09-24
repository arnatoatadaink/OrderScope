#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"
EXPECTED_VERSION=59
EXPECTED_THROUGH="2026-09-23T15:10:00.000Z"
FIRST_EXPECTED_START="2026-09-23T15:09:00.000Z"
RETENTION_MINUTES=1440

fail() { echo "ERROR: $*" >&2; exit 1; }

[[ "${ENV_NAME}" == "live-canary" ]] || fail "CLOUDFLARE_ENV must be live-canary"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || fail "wrong branch"
git diff --quiet || fail "worktree has unstaged changes"
git diff --cached --quiet || fail "worktree has staged changes"

now_epoch="$(date -u +%s)"
floor_epoch="$((now_epoch - RETENTION_MINUTES * 60))"
start_epoch="$(date -u -d "${FIRST_EXPECTED_START}" +%s)"
now_iso="$(date -u -d "@${now_epoch}" +%Y-%m-%dT%H:%M:%S.000Z)"
floor_iso="$(date -u -d "@${floor_epoch}" +%Y-%m-%dT%H:%M:%S.000Z)"

echo "L1-003 PB-07 stability observation read-only preflight"
echo "remoteMutation=false"
echo "observed_now=${now_iso}"
echo "retention_floor=${floor_iso}"
echo "expected_entry=v${EXPECTED_VERSION}/${EXPECTED_THROUGH}"
echo "first_expected_start=${FIRST_EXPECTED_START}"
echo

if (( floor_epoch > start_epoch )); then
  echo "PB-07 PRECONDITION BLOCKED: retention floor has passed the exact first expected range start." >&2
  echo "Do not activate PB-07 from this stale packet." >&2
  exit 3
fi

echo "== safe baseline =="
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2)); throw new Error("unsafe deployed baseline");
}
console.log(JSON.stringify({mode:h.mode,news:h.news?.mode,feed:h.feed},null,2));
NODE
code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${code}" == "404" ]] || fail "historical recovery endpoint must be closed; HTTP=${code}"

echo
echo "== control / exact NVDA entry =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT 1 AS control_pass;

SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}';

SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS pb07_entry_ok
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}'
  AND version=${EXPECTED_VERSION}
  AND complete_through='${EXPECTED_THROUGH}'
  AND source_observed_through='${EXPECTED_THROUGH}'
  AND state='COMPLETE'
  AND missing_ranges_json='[]'
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;

SELECT COUNT(*) AS unresolved_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND finished_at IS NULL AND outcome IS NULL;
"

echo
echo "== canary competition snapshot =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT coverage_key, symbol, interval, session_scope, logical_data_variant,
       complete_through, source_observed_through, state, missing_ranges_json,
       version, blocker_json, retry_not_before
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
echo "== recent NVDA normal-scheduler evidence =="
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
echo "PB-07 read-only preflight complete."
echo "Required before authorization:"
echo "  retention_floor <= ${FIRST_EXPECTED_START}"
echo "  pb07_entry_ok=1"
echo "  unresolved_attempts=0"
echo "  Worker=shadow / News=disabled / historical endpoint=404"
echo "  review competition snapshot to freeze bounded live opportunity count"
