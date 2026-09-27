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

echo "== PB-08 Phase B entry-packet preflight (read-only) =="
echo "remoteMutation=false"
echo "observed_now=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
echo "git_commit=$(git rev-parse HEAD)"
echo "wrangler_sha256=$(sha256sum wrangler.jsonc | awk '{print $1}')"
echo

echo "== deployed baseline =="
health="$(curl -fsS "${BASE_URL%/}/health")"
echo "${health}"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2)); throw new Error("unsafe deployed baseline");
}
NODE
code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${code}" == "404" ]] || fail "historical recovery endpoint must be closed"

echo
echo "== config identity =="
node --input-type=module - <<'NODE'
import fs from "node:fs";
const text=fs.readFileSync("wrangler.jsonc","utf8");
for(const expected of [
  '"WORKER_MODE": "shadow"',
  '"ALPACA_FEED": "iex"',
  '"UNIVERSE_PROFILE": "canary-v0.1"',
  '"ACQUISITION_RETENTION_MINUTES": "1440"',
  '"ACQUISITION_OVERLAP_1MIN_MINUTES": "1"',
  '"ACQUISITION_FINALIZATION_LAG_1MIN_MINUTES": "1"',
  '"ACQUISITION_MAX_JOBS_PER_TICK": "2"',
  '"ACQUISITION_MAX_BARS_PER_JOB": "100"',
  '"NEWS_ACQUISITION_ENABLED": "false"',
  '"HISTORICAL_RECOVERY_ENABLED": "false"',
]) {
  if(!text.includes(expected)) throw new Error(`missing config identity: ${expected}`);
}
console.log("config_identity_ok=1");
NODE

echo
echo "== Universe identity =="
node --experimental-strip-types --input-type=module - <<'NODE'
import { loadUniverseSnapshot } from "./src/universe.ts";
const u=loadUniverseSnapshot("canary-v0.1");
console.log(JSON.stringify({
  profile:"canary-v0.1",
  revision:u.revision,
  symbols:u.instruments.map(x=>x.symbol),
},null,2));
NODE

echo
echo "== NVDA checkpoint / scheduler evidence =="
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

SELECT started_at, finished_at, outcome, job_id, diagnostic_json
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
ORDER BY started_at DESC LIMIT 6;

SELECT digest_key, generated_at, payload_json
FROM latest_digest
WHERE digest_key='market'
LIMIT 1;
"

echo
echo "== canary checkpoint frontier =="
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
echo "PB-08 preflight complete."
echo "PB-08 freeze gate:"
echo "  PB-07 accepted"
echo "  Worker=shadow / News=disabled / historical endpoint=404"
echo "  NVDA COMPLETE / no gaps / no blocker / unresolved_attempts=0"
echo "  then determine whether NVDA is current enough for a fresh pause-gap experiment"
echo "No pause/resume or remote mutation is authorized by this script."
