#!/usr/bin/env bash
set -euo pipefail
# Requires explicit authorization for this new repair + continuation packet.
[[ "${CLOUDFLARE_ENV:-live-canary}" == live-canary ]] || exit 1
[[ "$(git branch --show-current)" == l1-003-local-market-recovery ]] || exit 1
git diff --quiet && git diff --cached --quiet
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=='shadow'||h.feed!=='iex'||h.news?.mode!=='disabled')throw new Error('unsafe baseline');
NODE
for endpoint in historical-recovery/nvda/local-evidence-next-chunk pb08/reproducible-absence/ack; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST "${BASE_URL%/}/control/${endpoint}")"
  [[ "${code}" == 404 ]] || { echo "control gate is open" >&2; exit 1; }
done
bash scripts/l1_003_pb08_local_acceptance.sh
echo '== exact single-row AMD repair; preserve NVDA v62 =='
repair="$(CLOUDFLARE_ENV=live-canary bash scripts/run-wrangler-with-env.sh d1 execute orderscope-state-live-canary --remote --json --file scripts/l1_003_pb08_sep25_amd_absence_ack.sql)"
echo "${repair}"
REPAIR="${repair}" node --input-type=module - <<'NODE'
const rows=JSON.parse(process.env.REPAIR).flatMap(g=>g.results??[]);
if(rows.length!==1||rows[0].coverage_key!=='AMD|1Min|REGULAR|stock:iex:raw'||rows[0].version!==46
  ||rows[0].complete_through!=='2026-09-25T16:49:00.000Z'||rows[0].state!=='COMPLETE'
  ||rows[0].missing_ranges_json!=='[]')throw new Error('AMD repair refused or mismatched');
NODE
bash scripts/l1_003_pb08_sep25_continuation_change_window.sh
