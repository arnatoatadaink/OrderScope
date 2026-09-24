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

echo "== PB-07 remote acceptance verification (read-only) =="
echo "remoteMutation=false"

health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2)); throw new Error("unsafe final baseline");
}
console.log("safe baseline: Worker=shadow News=disabled feed=iex");
NODE

CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}" --remote   --command "
SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS final_checkpoint_ok
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}'
  AND version=61
  AND complete_through='2026-09-23T18:28:00.000Z'
  AND source_observed_through='2026-09-23T18:28:00.000Z'
  AND state='COMPLETE'
  AND missing_ranges_json='[]'
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;

SELECT COUNT(*) AS canonical_bars
FROM normalized_bar
WHERE instrument_id='NVDA'
  AND interval='1Min'
  AND session_kind='REGULAR'
  AND logical_data_variant='stock:iex:raw'
  AND bar_start_utc >= '2026-09-23T15:09:00.000Z'
  AND bar_start_utc <  '2026-09-23T18:28:00.000Z';

SELECT COUNT(*) AS clean_nvda_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND started_at IN ('2026-09-24T14:39:23.000Z','2026-09-24T14:40:23.000Z')
  AND outcome='SUCCEEDED'
  AND COALESCE(json_extract(diagnostic_json,'$.conflicts'),0)=0
  AND COALESCE(json_extract(diagnostic_json,'$.rejected'),0)=0
  AND COALESCE(json_extract(diagnostic_json,'$.missing'),0)=0
  AND COALESCE(json_extract(diagnostic_json,'$.inserted'),0)
      + COALESCE(json_extract(diagnostic_json,'$.matched'),0)=100;

SELECT COUNT(*) AS bad_nvda_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND started_at >= '2026-09-24T14:39:23.000Z'
  AND started_at <= '2026-09-24T14:40:23.000Z'
  AND (outcome IS NULL OR outcome <> 'SUCCEEDED');

SELECT COUNT(*) AS clean_live_digests
FROM digest_history
WHERE digest_key='market'
  AND generated_at IN ('2026-09-24T14:39:23.000Z','2026-09-24T14:40:23.000Z')
  AND json_extract(payload_json,'$.mode')='live'
  AND json_extract(payload_json,'$.budget.withinBudget')=1;

SELECT COUNT(*) AS nonclean_market_summaries
FROM digest_history, json_each(json_extract(payload_json,'$.summaries'))
WHERE digest_key='market'
  AND generated_at IN ('2026-09-24T14:39:23.000Z','2026-09-24T14:40:23.000Z')
  AND json_extract(value,'$.outcome') <> 'SUCCEEDED';
"

echo
echo "Expected:"
echo "  final_checkpoint_ok=1"
echo "  canonical_bars=199"
echo "  clean_nvda_attempts=2"
echo "  bad_nvda_attempts=0"
echo "  clean_live_digests=2"
echo "  nonclean_market_summaries=0"
