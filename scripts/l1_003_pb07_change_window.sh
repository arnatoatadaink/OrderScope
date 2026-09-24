#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-https://orderscope-market-worker-live-canary.yuihout2.workers.dev}"
TEMP_CONFIG=".wrangler.pb07-live-canary.jsonc"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"

ENTRY_VERSION=59
ENTRY_THROUGH="2026-09-23T15:10:00.000Z"
FIRST_TARGET_VERSION=60
FIRST_TARGET_THROUGH="2026-09-23T16:49:00.000Z"
FINAL_TARGET_VERSION=61
FINAL_TARGET_THROUGH="2026-09-23T18:28:00.000Z"
FIRST_EXPECTED_START="2026-09-23T15:09:00.000Z"
MAX_OPPORTUNITIES=7
RETENTION_MINUTES=1440
LIVE_DEPLOYED=0

fail() { echo "ERROR: $*" >&2; exit 1; }

d1_json() {
  CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh d1 execute "${DB_NAME}"     --remote --json --command "$1"
}

json_scalar() {
  JSON_INPUT="$1" FIELD="$2" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.JSON_INPUT);
const rows=x?.[0]?.results ?? x?.results ?? [];
const row=rows[0] ?? {};
const v=row[process.env.FIELD];
if(v===undefined || v===null) process.exit(2);
process.stdout.write(String(v));
NODE
}

safe_close() {
  set +e
  if [[ "${LIVE_DEPLOYED}" == "1" ]]; then
    echo
    echo "== PB-07 safe close: restore checked-in shadow deployment =="
    CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy
    LIVE_DEPLOYED=0
  fi
  rm -f "${TEMP_CONFIG}"
  health="$(curl -fsS "${BASE_URL%/}/health" 2>/dev/null || true)"
  if [[ -n "${health}" ]]; then
    HEALTH="${health}" node --input-type=module - <<'NODE' || true
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled") process.exit(1);
console.log("safe baseline: Worker=shadow News=disabled");
NODE
  fi
}
trap safe_close EXIT

[[ "${ENV_NAME}" == "live-canary" ]] || fail "CLOUDFLARE_ENV must be live-canary"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || fail "wrong branch"
git diff --quiet || fail "worktree has unstaged changes"
git diff --cached --quiet || fail "worktree has staged changes"

now_epoch="$(date -u +%s)"
floor_epoch="$((now_epoch - RETENTION_MINUTES * 60))"
first_start_epoch="$(date -u -d "${FIRST_EXPECTED_START}" +%s)"
(( floor_epoch <= first_start_epoch )) || fail "moving retention floor has passed PB-07 first expected start; authorization packet is stale"

echo "== local acceptance before remote mutation =="
node --test --experimental-strip-types   src/pb07-stability.test.ts   src/pb07-opportunity-order.test.ts   src/pb06-handoff.test.ts   src/schedule.test.ts   src/job-priority.test.ts   src/execution.test.ts
npm run typecheck
git diff --check

echo
echo "== deployed safe baseline =="
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h=JSON.parse(process.env.HEALTH);
if(h.mode!=="shadow" || h.news?.mode!=="disabled" || h.feed!=="iex") {
  console.error(JSON.stringify(h,null,2)); process.exit(1);
}
NODE
pre_code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
[[ "${pre_code}" == "404" ]] || fail "historical recovery endpoint must remain closed"

echo
echo "== exact PB-07 remote entry =="
entry_json="$(d1_json "
SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS entry_ok
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}'
  AND version=${ENTRY_VERSION}
  AND complete_through='${ENTRY_THROUGH}'
  AND source_observed_through='${ENTRY_THROUGH}'
  AND state='COMPLETE'
  AND missing_ranges_json='[]'
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;
SELECT COUNT(*) AS unresolved_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND finished_at IS NULL AND outcome IS NULL;
")"
ENTRY_JSON="${entry_json}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.ENTRY_JSON);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const entry=Number(rows.find(r=>"entry_ok" in r)?.entry_ok);
const unresolved=Number(rows.find(r=>"unresolved_attempts" in r)?.unresolved_attempts);
if(entry!==1 || unresolved!==0) {
  console.error(JSON.stringify(rows,null,2));
  throw new Error("PB-07 exact entry failed");
}
NODE

baseline_digest_json="$(d1_json "SELECT generated_at FROM latest_digest WHERE digest_key='market' LIMIT 1;")"
baseline_digest="$(json_scalar "${baseline_digest_json}" generated_at)"
window_start="$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
echo "baseline_digest=${baseline_digest}"
echo "window_start=${window_start}"

echo
echo "== prepare temporary live config =="
node --input-type=module - <<'NODE'
import fs from "node:fs";
const source=fs.readFileSync("wrangler.jsonc","utf8");
const needle='"WORKER_MODE": "shadow"';
const count=source.split(needle).length-1;
if(count!==2) throw new Error("expected exactly two checked-in shadow modes");
fs.writeFileSync(".wrangler.pb07-live-canary.jsonc", source.replaceAll(needle,'"WORKER_MODE": "live"'));
NODE
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --dry-run --config "${TEMP_CONFIG}"

echo
echo "== activate temporary PB-07 live observation window =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --config "${TEMP_CONFIG}"
LIVE_DEPLOYED=1

last_digest="${baseline_digest}"
saw_v60=0
accepted=0

for opportunity in $(seq 1 "${MAX_OPPORTUNITIES}"); do
  echo
  echo "== wait for live scheduler opportunity ${opportunity}/${MAX_OPPORTUNITIES} =="
  observed=""
  digest_payload=""
  for probe in $(seq 1 90); do
    sleep 2
    digest_json="$(d1_json "SELECT generated_at, payload_json FROM latest_digest WHERE digest_key='market' LIMIT 1;")"
    probe_result="$(JSON_INPUT="${digest_json}" LAST="${last_digest}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.JSON_INPUT);
const row=(x?.[0]?.results??x?.results??[])[0];
if(!row || row.generated_at===process.env.LAST) process.exit(2);
const payload=JSON.parse(row.payload_json);
if(payload.mode!=="live") process.exit(2);
process.stdout.write(JSON.stringify({generatedAt:row.generated_at,payload}));
NODE
    )" && {
      observed="$(PROBE="${probe_result}" node --input-type=module -e 'const x=JSON.parse(process.env.PROBE);process.stdout.write(x.generatedAt)')"
      digest_payload="$(PROBE="${probe_result}" node --input-type=module -e 'const x=JSON.parse(process.env.PROBE);process.stdout.write(JSON.stringify(x.payload))')"
      break
    } || true
  done
  [[ -n "${observed}" ]] || fail "no distinct live scheduler digest observed"
  last_digest="${observed}"
  echo "opportunity_${opportunity}_digest=${observed}"

  PAYLOAD="${digest_payload}" node --input-type=module - <<'NODE'
const p=JSON.parse(process.env.PAYLOAD);
if(p.budget?.withinBudget!==true) {
  console.error(JSON.stringify(p.budget,null,2));
  throw new Error("scheduler budget regression");
}
const bad=(p.summaries??[]).filter(s=>s.outcome!=="SUCCEEDED");
if(bad.length) {
  console.error(JSON.stringify(bad,null,2));
  throw new Error("non-clean market scheduler outcome");
}
if(p.news?.mode!=="disabled") throw new Error("News became enabled");
NODE

  check_json="$(d1_json "
SELECT coverage_key, complete_through, source_observed_through, state,
       missing_ranges_json, version, blocker_json, retry_not_before
FROM coverage_checkpoint WHERE coverage_key='${COVERAGE_KEY}';

SELECT started_at, finished_at, outcome, job_id, diagnostic_json
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}' AND started_at >= '${window_start}'
ORDER BY started_at ASC;

SELECT COUNT(*) AS bad_nvda_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}' AND started_at >= '${window_start}'
  AND (outcome IS NULL OR outcome <> 'SUCCEEDED');
")"
  echo "${check_json}"

  state="$(CHECK_JSON="${check_json}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.CHECK_JSON);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const cp=rows.find(r=>r.coverage_key==="NVDA|1Min|REGULAR|stock:iex:raw");
const attempts=rows.filter(r=>r.job_id && r.started_at);
const bad=Number(rows.find(r=>"bad_nvda_attempts" in r)?.bad_nvda_attempts ?? 0);
if(bad!==0) throw new Error("bad/interrupted NVDA attempt observed");
for(const a of attempts) {
  const d=JSON.parse(a.diagnostic_json??"{}");
  if(a.outcome!=="SUCCEEDED"
    || Number(d.conflicts??0)!==0
    || Number(d.rejected??0)!==0
    || Number(d.missing??0)!==0
    || Number(d.inserted??0)+Number(d.matched??0)!==100) {
    console.error(JSON.stringify(a,null,2));
    throw new Error("NVDA attempt is not clean");
  }
}
if(cp?.version===60
  && cp.complete_through==="2026-09-23T16:49:00.000Z"
  && cp.source_observed_through==="2026-09-23T16:49:00.000Z"
  && cp.state==="COMPLETE"
  && cp.missing_ranges_json==="[]"
  && cp.blocker_json===null
  && cp.retry_not_before===null
  && attempts.length===1) process.stdout.write("v60");
else if(cp?.version===61
  && cp.complete_through==="2026-09-23T18:28:00.000Z"
  && cp.source_observed_through==="2026-09-23T18:28:00.000Z"
  && cp.state==="COMPLETE"
  && cp.missing_ranges_json==="[]"
  && cp.blocker_json===null
  && cp.retry_not_before===null
  && attempts.length===2) process.stdout.write("v61");
else process.stdout.write("waiting");
NODE
  )"

  if [[ "${state}" == "v60" ]]; then
    saw_v60=1
    echo "PB-07 first clean NVDA advance observed: v60 / ${FIRST_TARGET_THROUGH}"
  elif [[ "${state}" == "v61" ]]; then
    [[ "${saw_v60}" == "1" ]] || fail "v61 observed without separately observed v60 stability step"
    accepted=1
    echo "PB-07 second clean NVDA advance observed: v61 / ${FINAL_TARGET_THROUGH}"
    break
  fi
done

[[ "${accepted}" == "1" ]] || fail "PB-07 two clean NVDA advances not observed within seven Cron opportunities"

echo
echo "== exact PB-07 final evidence =="
final_json="$(d1_json "
SELECT CASE WHEN COUNT(*)=1 THEN 1 ELSE 0 END AS final_checkpoint_ok
FROM coverage_checkpoint
WHERE coverage_key='${COVERAGE_KEY}'
  AND version=${FINAL_TARGET_VERSION}
  AND complete_through='${FINAL_TARGET_THROUGH}'
  AND source_observed_through='${FINAL_TARGET_THROUGH}'
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
  AND started_at >= '${window_start}'
  AND outcome='SUCCEEDED'
  AND COALESCE(json_extract(diagnostic_json,'$.conflicts'),0)=0
  AND COALESCE(json_extract(diagnostic_json,'$.rejected'),0)=0
  AND COALESCE(json_extract(diagnostic_json,'$.missing'),0)=0
  AND COALESCE(json_extract(diagnostic_json,'$.inserted'),0)
      + COALESCE(json_extract(diagnostic_json,'$.matched'),0)=100;

SELECT COUNT(*) AS bad_nvda_attempts
FROM acquisition_attempt
WHERE coverage_key='${COVERAGE_KEY}'
  AND started_at >= '${window_start}'
  AND (outcome IS NULL OR outcome <> 'SUCCEEDED');
")"
FINAL_JSON="${final_json}" node --input-type=module - <<'NODE'
const x=JSON.parse(process.env.FINAL_JSON);
const rows=(Array.isArray(x)?x:[x]).flatMap(g=>g.results??[]);
const get=k=>Number(rows.find(r=>k in r)?.[k]);
if(get("final_checkpoint_ok")!==1
  || get("canonical_bars")!==199
  || get("clean_nvda_attempts")!==2
  || get("bad_nvda_attempts")!==0) {
  console.error(JSON.stringify(rows,null,2));
  throw new Error("PB-07 final evidence mismatch");
}
console.log(JSON.stringify({
  final_checkpoint_ok:get("final_checkpoint_ok"),
  canonical_bars:get("canonical_bars"),
  clean_nvda_attempts:get("clean_nvda_attempts"),
  bad_nvda_attempts:get("bad_nvda_attempts"),
},null,2));
NODE

echo
echo "PB-07 stability observation: ACCEPTED REMOTELY at v61 / ${FINAL_TARGET_THROUGH}"
echo "Safe-close will restore checked-in shadow deployment."
