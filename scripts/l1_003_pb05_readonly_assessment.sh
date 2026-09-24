#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-}"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"
EXPECTED_VERSION=58
EXPECTED_THROUGH="2026-09-22T20:00:00.000Z"
NEXT_SESSION_OPEN="${PB05_NEXT_SESSION_OPEN:-2026-09-23T13:30:00.000Z}"
RETENTION_MINUTES="${PB05_RETENTION_MINUTES:-1440}"

[[ "${ENV_NAME}" == "live-canary" ]] || { echo "ERROR: CLOUDFLARE_ENV must be live-canary" >&2; exit 1; }
[[ -n "${BASE_URL}" ]] || { echo "ERROR: set ORDERSCOPE_LIVE_CANARY_URL" >&2; exit 1; }

now_epoch="$(date -u +%s)"
floor_epoch="$((now_epoch - RETENTION_MINUTES * 60))"
next_open_epoch="$(date -u -d "${NEXT_SESSION_OPEN}" +%s)"
now_iso="$(date -u -d "@${now_epoch}" +%Y-%m-%dT%H:%M:%S.000Z)"
floor_iso="$(date -u -d "@${floor_epoch}" +%Y-%m-%dT%H:%M:%S.000Z)"

echo "L1-003 PB-05 read-only handoff assessment"
echo "remoteMutation=false"
echo "observed_now=${now_iso}"
echo "retention_floor=${floor_iso}"
echo "historical_target=${EXPECTED_THROUGH}"
echo "next_session_open=${NEXT_SESSION_OPEN}"

if (( floor_epoch > next_open_epoch )); then
  echo "PB-05: BLOCKED — moving retention floor has passed the frozen Sep23 Regular open." >&2
  echo "Re-run PB-01 with an authoritative newer handoff target before any further historical mutation." >&2
  exit 3
fi

echo
echo "== safe baseline =="
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h = JSON.parse(process.env.HEALTH);
if (h.mode !== "shadow" || h.news?.mode !== "disabled") {
  console.error(JSON.stringify(h, null, 2));
  throw new Error("live-canary is not shadow/news-disabled");
}
NODE
code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${code}" == "404" ]] || { echo "ERROR: recovery endpoint is not closed; HTTP=${code}" >&2; exit 1; }

echo
echo "== exact checkpoint / unresolved state =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote --command "
SELECT
  coverage_key, complete_through, source_observed_through, state,
  missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint
WHERE coverage_key = '${COVERAGE_KEY}';

SELECT COUNT(*) AS unresolved_attempts
FROM acquisition_attempt
WHERE coverage_key = '${COVERAGE_KEY}'
  AND finished_at IS NULL
  AND outcome IS NULL;

SELECT CASE WHEN COUNT(*) = 1 THEN 1 ELSE 0 END AS pb05_checkpoint_ok
FROM coverage_checkpoint
WHERE coverage_key = '${COVERAGE_KEY}'
  AND complete_through = '${EXPECTED_THROUGH}'
  AND source_observed_through = '${EXPECTED_THROUGH}'
  AND state = 'COMPLETE'
  AND missing_ranges_json = '[]'
  AND version = ${EXPECTED_VERSION}
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;

SELECT COUNT(*) AS sep09_to_sep22_canonical_bars
FROM normalized_bar
WHERE instrument_id = 'NVDA'
  AND interval = '1Min'
  AND session_kind = 'REGULAR'
  AND logical_data_variant = 'stock:iex:raw'
  AND bar_start_utc >= '2026-09-09T13:30:00.000Z'
  AND bar_start_utc <  '2026-09-22T20:00:00.000Z';
"

echo
echo "Expected read-only acceptance values:"
echo "  pb05_checkpoint_ok=1"
echo "  unresolved_attempts=0"
echo "  sep09_to_sep22_canonical_bars=3899"
echo "  retention_floor <= ${NEXT_SESSION_OPEN}"
echo
echo "PB-05 assessment issued no mutation statements."
