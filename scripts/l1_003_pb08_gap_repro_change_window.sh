#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
TEMP_CONFIG=".wrangler.pb08-gap-repro-live-canary.jsonc"
LIVE_DEPLOYED=0
RETENTION_MINUTES=1440
EARLIEST_RETRY_START="2026-09-24T14:31:00.000Z"

fail(){ echo "ERROR: $*" >&2; exit 1; }

d1_json(){
  CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}"     --remote --json --command "$1"
}

safe_close(){
  set +e
  if [[ "${LIVE_DEPLOYED}" == "1" ]]; then
    echo
    echo "== restore checked-in Shadow deployment =="
    CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy
    LIVE_DEPLOYED=0
  fi
  rm -f "${TEMP_CONFIG}"
}
trap safe_close EXIT

[[ "${ENV_NAME}" == "live-canary" ]] || fail "wrong environment"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || fail "wrong branch"
git diff --quiet || fail "unstaged changes"
git diff --cached --quiet || fail "staged changes"

now_epoch="$(date -u +%s)"
floor_epoch="$((now_epoch - RETENTION_MINUTES * 60))"
retry_epoch="$(date -u -d "${EARLIEST_RETRY_START}" +%s)"
(( floor_epoch <= retry_epoch )) || fail "AMD/QQQ retry range is outside retention; re-freeze required"

echo "== PB-08 local acceptance before gap verification =="
bash scripts/l1_003_pb08_local_acceptance.sh

health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2));
  throw new Error("unsafe baseline");
}
NODE

code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${code}" == "404" ]] || fail "historical recovery endpoint must remain closed"

echo "== exact gap-verification entry =="
entry="$(d1_json "
SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint
WHERE coverage_key IN (
  'AMD|1Min|REGULAR|stock:iex:raw',
  'QQQ|1Min|REGULAR|stock:iex:raw',
  'NVDA|1Min|REGULAR|stock:iex:raw'
)
ORDER BY coverage_key;

SELECT COUNT(*) AS unresolved
FROM acquisition_attempt
WHERE coverage_key IN (
  'AMD|1Min|REGULAR|stock:iex:raw',
  'QQQ|1Min|REGULAR|stock:iex:raw',
  'NVDA|1Min|REGULAR|stock:iex:raw'
)
AND finished_at IS NULL AND outcome IS NULL;
")"

ENTRY="${entry}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.ENTRY);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const by=new Map(rows.filter(r=>r.coverage_key).map(r=>[r.coverage_key,r]));
const amd=by.get("AMD|1Min|REGULAR|stock:iex:raw");
const qqq=by.get("QQQ|1Min|REGULAR|stock:iex:raw");
const nvda=by.get("NVDA|1Min|REGULAR|stock:iex:raw");
const unresolved=Number(rows.find(r=>"unresolved" in r)?.unresolved??-1);
function exact(r,v,through,missing){
  return r && Number(r.version)===v && r.complete_through===through
    && r.state==="PARTIAL" && r.missing_ranges_json===missing
    && r.blocker_json===null;
}
if(!exact(amd,41,"2026-09-24T14:49:00.000Z",
  '[{"startInclusive":"2026-09-24T14:49:00.000Z","endExclusive":"2026-09-24T14:50:00.000Z"}]')) {
  console.error(amd); throw new Error("AMD entry changed");
}
if(!exact(qqq,10,"2026-09-24T14:32:00.000Z",
  '[{"startInclusive":"2026-09-24T14:32:00.000Z","endExclusive":"2026-09-24T14:33:00.000Z"}]')) {
  console.error(qqq); throw new Error("QQQ entry changed");
}
if(!nvda || Number(nvda.version)!==61 || nvda.complete_through!=="2026-09-23T18:28:00.000Z"
  || nvda.state!=="COMPLETE" || nvda.missing_ranges_json!=="[]") {
  console.error(nvda); throw new Error("NVDA frozen entry changed");
}
if(unresolved!==0) throw new Error("unresolved attempt exists");
NODE

baseline="$(d1_json "SELECT generated_at FROM latest_digest WHERE digest_key='market' LIMIT 1;")"
last_digest="$(J="${baseline}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.J); const r=(x?.[0]?.results??x?.results??[])[0];
if(!r?.generated_at) process.exit(2); process.stdout.write(r.generated_at);
NODE
)"
window_start="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"

node --input-type=module - <<'NODE'
import fs from "node:fs";
const s=fs.readFileSync("wrangler.jsonc","utf8");
const needle='"WORKER_MODE": "shadow"';
if(s.split(needle).length-1!==2) throw new Error("unexpected shadow count");
fs.writeFileSync(".wrangler.pb08-gap-repro-live-canary.jsonc",
  s.replaceAll(needle,'"WORKER_MODE": "live"'));
NODE

CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --dry-run --config "${TEMP_CONFIG}"
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --config "${TEMP_CONFIG}"
LIVE_DEPLOYED=1

echo "== wait for exactly one live scheduler opportunity =="
observed=""
payload=""
for _ in $(seq 1 90); do
  sleep 2
  digest="$(d1_json "SELECT generated_at,payload_json FROM latest_digest WHERE digest_key='market' LIMIT 1;")"
  probe="$(J="${digest}" LAST="${last_digest}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.J); const r=(x?.[0]?.results??x?.results??[])[0];
if(!r || r.generated_at===process.env.LAST) process.exit(2);
const p=JSON.parse(r.payload_json);
if(p.mode!=="live") process.exit(2);
if(p.budget?.withinBudget!==true) throw new Error("budget regression");
if(p.news?.mode!=="disabled") throw new Error("News became enabled");
process.stdout.write(JSON.stringify({generatedAt:r.generated_at,payload:p}));
NODE
  )" && {
    observed="$(P="${probe}" node --input-type=module -e 'process.stdout.write(JSON.parse(process.env.P).generatedAt)')"
    payload="$(P="${probe}" node --input-type=module -e 'process.stdout.write(JSON.stringify(JSON.parse(process.env.P).payload))')"
    break
  } || true
done
[[ -n "${observed}" ]] || fail "no live digest observed"
echo "digest=${observed}"

PAYLOAD="${payload}" node --input-type=module - <<'NODE'
const p=JSON.parse(process.env.PAYLOAD);
const s=p.summaries??[];
if(s.length!==2) {
  console.error(JSON.stringify(s,null,2));
  throw new Error("expected exactly two selected market jobs");
}
for(const x of s){
  if(!["SUCCEEDED","PARTIAL"].includes(x.outcome)
    || Number(x.conflicts??0)!==0 || Number(x.rejected??0)!==0) {
    console.error(JSON.stringify(x,null,2));
    throw new Error("unexpected verification outcome");
  }
}
NODE

echo "== verification evidence =="
result="$(d1_json "
SELECT coverage_key, started_at, finished_at, outcome, job_id, diagnostic_json
FROM acquisition_attempt
WHERE started_at >= '${window_start}'
ORDER BY started_at, coverage_key;

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
echo "${result}"

RESULT="${result}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.RESULT);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const attempts=rows.filter(r=>r.job_id);
if(attempts.length!==2) throw new Error("expected exactly two attempts");
const keys=attempts.map(a=>a.coverage_key).sort();
const expected=[
  "AMD|1Min|REGULAR|stock:iex:raw",
  "QQQ|1Min|REGULAR|stock:iex:raw",
];
if(JSON.stringify(keys)!==JSON.stringify(expected)) {
  console.error(attempts); throw new Error("verification selected unexpected coverage keys");
}
const by=new Map(rows.filter(r=>r.coverage_key && !r.job_id).map(r=>[r.coverage_key,r]));
const nvda=by.get("NVDA|1Min|REGULAR|stock:iex:raw");
if(!nvda || Number(nvda.version)!==61 || nvda.complete_through!=="2026-09-23T18:28:00.000Z") {
  throw new Error("NVDA changed during gap verification");
}
const specs={
  "AMD|1Min|REGULAR|stock:iex:raw":{
    oldVersion:41, repairedThrough:"2026-09-24T14:50:00.000Z",
    missing:'[{"startInclusive":"2026-09-24T14:49:00.000Z","endExclusive":"2026-09-24T14:50:00.000Z"}]'
  },
  "QQQ|1Min|REGULAR|stock:iex:raw":{
    oldVersion:10, repairedThrough:"2026-09-24T14:33:00.000Z",
    missing:'[{"startInclusive":"2026-09-24T14:32:00.000Z","endExclusive":"2026-09-24T14:33:00.000Z"}]'
  }
};
for(const a of attempts){
  const cp=by.get(a.coverage_key); const s=specs[a.coverage_key];
  const d=JSON.parse(a.diagnostic_json??"{}");
  if(Number(d.conflicts??0)!==0 || Number(d.rejected??0)!==0) throw new Error("dirty attempt");
  if(a.outcome==="SUCCEEDED"){
    if(Number(d.missing??-1)!==0 || cp.state!=="COMPLETE" || cp.missing_ranges_json!=="[]"
      || cp.complete_through!==s.repairedThrough || Number(cp.version)!==s.oldVersion+1) {
      console.error({a,cp}); throw new Error("invalid REPAIRED result");
    }
    console.log(a.coverage_key.split("|")[0]+": REPAIRED");
  } else if(a.outcome==="PARTIAL"){
    if(Number(d.missing??-1)!==1 || cp.state!=="PARTIAL" || cp.missing_ranges_json!==s.missing
      || Number(cp.version)!==s.oldVersion+1) {
      console.error({a,cp}); throw new Error("invalid REPRODUCED result");
    }
    console.log(a.coverage_key.split("|")[0]+": REPRODUCED");
  } else throw new Error("unexpected attempt outcome");
}
NODE

echo "PB-08 AMD/QQQ gap reproducibility verification: COMPLETE"
echo "Safe-close will restore checked-in Shadow deployment."
