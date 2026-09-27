#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"
EXPECTED_VERSION=58
EXPECTED_THROUGH="2026-09-22T20:00:00.000Z"
HANDOFF_OPEN="2026-09-23T13:30:00.000Z"
HANDOFF_CLOSE="2026-09-23T20:00:00.000Z"
RETENTION_MINUTES=1440

fail() { echo "ERROR: $*" >&2; exit 1; }

[[ "${ENV_NAME}" == "live-canary" ]] || fail "CLOUDFLARE_ENV must be live-canary"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || fail "wrong branch"
git diff --quiet || fail "worktree has unstaged changes"
git diff --cached --quiet || fail "worktree has staged changes"

now_epoch="$(date -u +%s)"
floor_epoch="$((now_epoch - RETENTION_MINUTES * 60))"
open_epoch="$(date -u -d "${HANDOFF_OPEN}" +%s)"
now_iso="$(date -u -d "@${now_epoch}" +%Y-%m-%dT%H:%M:%S.000Z)"
floor_iso="$(date -u -d "@${floor_epoch}" +%Y-%m-%dT%H:%M:%S.000Z)"

echo "L1-003 PB-06 normal-scheduler handoff read-only preflight"
echo "remoteMutation=false"
echo "observed_now=${now_iso}"
echo "retention_floor=${floor_iso}"
echo "handoff_session=2026-09-23 REGULAR"
echo "handoff_open=${HANDOFF_OPEN}"
echo "handoff_close=${HANDOFF_CLOSE}"
echo

if (( floor_epoch > open_epoch )); then
  echo "PB-06 PRECONDITION BLOCKED: retention floor has passed Sep23 Regular open." >&2
  echo "PB-01/PB-04 must re-freeze a newer handoff boundary; do not activate scheduler." >&2
  exit 3
fi

echo "== health safe baseline =="
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled") {
  console.error(JSON.stringify(h,null,2));
  throw new Error("expected shadow/news-disabled safe baseline");
}
console.log(JSON.stringify({mode:h.mode,news:h.news?.mode,feed:h.feed},null,2));
NODE

code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${code}" == "404" ]] || fail "historical recovery endpoint must be closed; HTTP=${code}"
echo "historical_recovery_endpoint=404"

echo
echo "== Cloudflare identity =="
npx wrangler whoami

echo
echo "== control read =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "SELECT 1 AS control_pass;"

echo
echo "== NVDA exact PB-05 handoff checkpoint =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}';

SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS nvda_handoff_ok
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}'
  AND complete_through='${EXPECTED_THROUGH}'
  AND source_observed_through='${EXPECTED_THROUGH}'
  AND state='COMPLETE'
  AND missing_ranges_json='[]'
  AND version=${EXPECTED_VERSION}
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;

SELECT COUNT(*) AS unresolved_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND finished_at IS NULL
  AND outcome IS NULL;
"

echo
echo "== canary scheduler competition snapshot =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT coverage_key, symbol, interval, session_scope, logical_data_variant,
       complete_through, state, missing_ranges_json, version, blocker_json,
       retry_not_before
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
echo "== latest scheduler digest =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT digest_key, generated_at, payload_json
FROM latest_digest
ORDER BY generated_at DESC
LIMIT 1;
"

echo
echo "PB-06 read-only preflight complete."
echo "Required acceptance before activation:"
echo "  retention_floor <= ${HANDOFF_OPEN}"
echo "  nvda_handoff_ok=1"
echo "  unresolved_attempts=0"
echo "  Worker=shadow / News=disabled / historical endpoint=404"
echo "  review canary competition snapshot before freezing scheduler observation window"
