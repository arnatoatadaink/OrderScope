#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
TEMP_CONFIG=".wrangler.pb08-absence-ack-live-canary.jsonc"
TOKEN=""
SECRET_SET=0
TEMP_GATE_DEPLOYED=0
CLOSED=0

fail(){ echo "ERROR: $*" >&2; exit 1; }

d1_json(){
  CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}"     --remote --json --command "$1"
}

wait_for_code(){
  local expected="$1"
  local attempts="${2:-15}"
  local code=""
  for ((i=1;i<=attempts;i+=1)); do
    code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST       "${BASE_URL%/}/control/pb08/reproducible-absence/ack" || true)"
    if [[ "${code}" == "${expected}" ]]; then
      echo "ack endpoint HTTP=${code} after probe ${i}/${attempts}"
      return 0
    fi
    sleep 2
  done
  echo "ack endpoint did not reach HTTP ${expected}; last HTTP=${code}" >&2
  return 1
}

safe_close(){
  local status=$?
  if [[ "${CLOSED}" -eq 1 ]]; then
    exit "${status}"
  fi
  CLOSED=1
  set +e
  echo
  echo "== PB-08 absence-ack safe close =="

  if [[ "${TEMP_GATE_DEPLOYED}" -eq 1 ]]; then
    echo "Restoring checked-in gate=false Shadow deployment..."
    CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --config wrangler.jsonc
    TEMP_GATE_DEPLOYED=0
  fi

  if [[ "${SECRET_SET}" -eq 1 ]]; then
    echo "Deleting temporary HISTORICAL_RECOVERY_CONTROL_TOKEN..."
    printf 'y\n' | CLOUDFLARE_ENV="${ENV_NAME}"       bash scripts/run-wrangler-with-env.sh secret delete HISTORICAL_RECOVERY_CONTROL_TOKEN
    SECRET_SET=0
  fi

  rm -f "${TEMP_CONFIG}" .pb08-absence-ack-response.json

  if wait_for_code "404" 15; then
    echo "final ack endpoint reached expected 404"
  else
    echo "WARNING: final ack endpoint did not confirm 404 inside probe window" >&2
    status=1
  fi

  health="$(curl -fsS "${BASE_URL%/}/health" 2>/dev/null || true)"
  if [[ -n "${health}" ]]; then
    HEALTH="${health}" node --input-type=module - <<'NODE' || status=1
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2));
  process.exit(1);
}
console.log("safe baseline: Worker=shadow News=disabled feed=iex");
NODE
  fi

  exit "${status}"
}
trap safe_close EXIT INT TERM

[[ "${ENV_NAME}" == "live-canary" ]] || fail "wrong environment"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || fail "wrong branch"
git diff --quiet || fail "unstaged changes"
git diff --cached --quiet || fail "staged changes"

echo "== PB-08 local acceptance before absence acknowledgement =="
bash scripts/l1_003_pb08_local_acceptance.sh

echo
echo "== safe baseline / closed gate =="
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2));
  throw new Error("unsafe baseline");
}
NODE
wait_for_code "404" 5 || fail "ack endpoint must be closed before change window"

echo
echo "== exact remote acknowledgement entry =="
entry="$(d1_json "
SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS amd_ok
FROM coverage_checkpoint
WHERE coverage_key='AMD|1Min|REGULAR|stock:iex:raw'
  AND version=42
  AND complete_through='2026-09-24T14:49:00.000Z'
  AND source_observed_through='2026-09-24T14:50:00.000Z'
  AND state='PARTIAL'
  AND missing_ranges_json='[{"startInclusive":"2026-09-24T14:49:00.000Z","endExclusive":"2026-09-24T14:50:00.000Z"}]'
  AND blocker_json IS NULL;

SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS qqq_ok
FROM coverage_checkpoint
WHERE coverage_key='QQQ|1Min|REGULAR|stock:iex:raw'
  AND version=11
  AND complete_through='2026-09-24T14:32:00.000Z'
  AND source_observed_through='2026-09-24T14:33:00.000Z'
  AND state='PARTIAL'
  AND missing_ranges_json='[{"startInclusive":"2026-09-24T14:32:00.000Z","endExclusive":"2026-09-24T14:33:00.000Z"}]'
  AND blocker_json IS NULL;

SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS nvda_ok
FROM coverage_checkpoint
WHERE coverage_key='NVDA|1Min|REGULAR|stock:iex:raw'
  AND version=61
  AND complete_through='2026-09-23T18:28:00.000Z'
  AND source_observed_through='2026-09-23T18:28:00.000Z'
  AND state='COMPLETE'
  AND missing_ranges_json='[]'
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;

SELECT COUNT(*) AS unresolved_canary_attempts
FROM acquisition_attempt
WHERE coverage_key IN (
  'SPY|1Min|REGULAR|stock:iex:raw',
  'QQQ|1Min|REGULAR|stock:iex:raw',
  'NVDA|1Min|REGULAR|stock:iex:raw',
  'AMD|1Min|REGULAR|stock:iex:raw',
  'BTCUSD|1Min|ALL_TRADING|crypto:us'
)
AND finished_at IS NULL AND outcome IS NULL;
")"

echo "${entry}"

ENTRY="${entry}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.ENTRY);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const get=(key)=>Number(rows.find(r=>key in r)?.[key] ?? -1);
const evidence={
  amd_ok:get("amd_ok"),
  qqq_ok:get("qqq_ok"),
  nvda_ok:get("nvda_ok"),
  unresolved_canary_attempts:get("unresolved_canary_attempts"),
};
console.log(JSON.stringify(evidence,null,2));
if(evidence.amd_ok!==1
  || evidence.qqq_ok!==1
  || evidence.nvda_ok!==1
  || evidence.unresolved_canary_attempts!==0) {
  throw new Error("PB-08 absence acknowledgement exact entry failed");
}
NODE

echo
echo "== prepare temporary closed-token / open-gate deployment =="
TOKEN="$(node -e 'console.log(require("node:crypto").randomBytes(32).toString("hex"))')"
printf '%s\n' "${TOKEN}" | CLOUDFLARE_ENV="${ENV_NAME}"   bash scripts/run-wrangler-with-env.sh secret put HISTORICAL_RECOVERY_CONTROL_TOKEN
SECRET_SET=1

node --input-type=module - <<'NODE'
import fs from "node:fs";
const source=fs.readFileSync("wrangler.jsonc","utf8");
const needle='"PB08_ABSENCE_ACK_ENABLED": "false"';
const count=source.split(needle).length-1;
if(count!==2) throw new Error("expected exactly two checked-in PB08 ack gates");
fs.writeFileSync(
  ".wrangler.pb08-absence-ack-live-canary.jsonc",
  source.replaceAll(needle,'"PB08_ABSENCE_ACK_ENABLED": "true"'),
);
NODE

CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --dry-run --config "${TEMP_CONFIG}"
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --config "${TEMP_CONFIG}"
TEMP_GATE_DEPLOYED=1

wait_for_code "401" 15 || fail "ack endpoint did not open behind authentication"

echo
echo "== execute one exact absence acknowledgement =="
http_code="$(curl -sS -o .pb08-absence-ack-response.json -w '%{http_code}'   -X POST   -H "Authorization: Bearer ${TOKEN}"   "${BASE_URL%/}/control/pb08/reproducible-absence/ack")"

cat .pb08-absence-ack-response.json
echo

[[ "${http_code}" == "200" ]] || fail "ack endpoint returned HTTP ${http_code}"

RESPONSE="$(cat .pb08-absence-ack-response.json)" node --input-type=module - <<'NODE'
const r=JSON.parse(process.env.RESPONSE);
if(r.accepted!==true
  || r.evidence?.reason!=="REPRODUCIBLE_PROVIDER_ABSENCE"
  || Number(r.evidence?.observations)!==2
  || !Array.isArray(r.checkpoints)
  || r.checkpoints.length!==2) {
  console.error(JSON.stringify(r,null,2));
  throw new Error("ack response mismatch");
}
const by=new Map(r.checkpoints.map(c=>[c.coverageKey,c]));
const amd=by.get("AMD|1Min|REGULAR|stock:iex:raw");
const qqq=by.get("QQQ|1Min|REGULAR|stock:iex:raw");
if(!amd || amd.version!==43 || amd.completeThrough!=="2026-09-24T14:50:00.000Z"
  || amd.state!=="COMPLETE" || amd.missingRanges.length!==0) throw new Error("AMD ack mismatch");
if(!qqq || qqq.version!==12 || qqq.completeThrough!=="2026-09-24T14:33:00.000Z"
  || qqq.state!=="COMPLETE" || qqq.missingRanges.length!==0) throw new Error("QQQ ack mismatch");
NODE

echo
echo "== exact post-ack evidence =="
after="$(d1_json "
SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint
WHERE coverage_key IN (
  'AMD|1Min|REGULAR|stock:iex:raw',
  'QQQ|1Min|REGULAR|stock:iex:raw',
  'NVDA|1Min|REGULAR|stock:iex:raw'
)
ORDER BY coverage_key;
")"
echo "${after}"

AFTER="${after}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.AFTER);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const by=new Map(rows.map(r=>[r.coverage_key,r]));
const amd=by.get("AMD|1Min|REGULAR|stock:iex:raw");
const qqq=by.get("QQQ|1Min|REGULAR|stock:iex:raw");
const nvda=by.get("NVDA|1Min|REGULAR|stock:iex:raw");

for(const [name,r,v,t] of [
  ["AMD",amd,43,"2026-09-24T14:50:00.000Z"],
  ["QQQ",qqq,12,"2026-09-24T14:33:00.000Z"],
]){
  if(!r || Number(r.version)!==v || r.complete_through!==t
    || r.source_observed_through!==t
    || r.state!=="COMPLETE"
    || r.missing_ranges_json!=="[]"
    || r.blocker_json!==null
    || r.retry_not_before!==null) {
    console.error({name,r}); throw new Error(name+" post-ack mismatch");
  }
}

if(!nvda || Number(nvda.version)!==61
  || nvda.complete_through!=="2026-09-23T18:28:00.000Z"
  || nvda.state!=="COMPLETE"
  || nvda.missing_ranges_json!=="[]") throw new Error("NVDA changed during ack");
NODE

echo
echo "PB-08 reproducible-provider-absence acknowledgement: ACCEPTED REMOTELY"
echo "Safe-close will restore gate=false Shadow and delete the temporary token."
