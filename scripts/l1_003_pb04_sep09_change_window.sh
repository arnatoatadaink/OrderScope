#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${CLOUDFLARE_ENV:-live-canary}"
DB_NAME="${ORDERSCOPE_LIVE_CANARY_D1_NAME:-orderscope-state-live-canary}"
BASE_URL="${ORDERSCOPE_LIVE_CANARY_URL:-}"
PACKET="${PB04_PACKET:-var/l1-003/local-market-recovery/nvda/PB04_NVDA_2026-09-09_REMOTE_PACKET.json}"
EVIDENCE="${PB04_EVIDENCE:-var/l1-003/local-market-recovery/nvda/NVDA_1Min_REGULAR_2026-09-09.json}"
COVERAGE_KEY="NVDA|1Min|REGULAR|stock:iex:raw"
TEMP_CONFIG=".wrangler.pb04-live-canary.jsonc"
BODY_FILE=".pb04-local-evidence-body.json"
RESPONSE_FILE=".pb04-response.json"
TOKEN=""
SECRET_SET=0
TEMP_GATE_DEPLOYED=0
CLOSED=0

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

d1_json() {
  CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh     d1 execute "${DB_NAME}" --remote --json --command "$1"
}

assert_single_json_value() {
  local payload="$1"
  local field="$2"
  local expected="$3"
  JSON_PAYLOAD="${payload}" FIELD="${field}" EXPECTED="${expected}" node --input-type=module - <<'NODE'
const payload = JSON.parse(process.env.JSON_PAYLOAD);
const result = Array.isArray(payload) ? payload[0] : payload;
const row = result?.results?.[0];
if (!row || String(row[process.env.FIELD]) !== process.env.EXPECTED) {
  console.error(JSON.stringify({field: process.env.FIELD, expected: process.env.EXPECTED, row}, null, 2));
  process.exit(1);
}
NODE
}

safe_close() {
  local status=$?
  if [[ "${CLOSED}" -eq 1 ]]; then
    exit "${status}"
  fi
  CLOSED=1
  set +e
  echo
  echo "== PB-04 safe close =="
  if [[ "${TEMP_GATE_DEPLOYED}" -eq 1 ]]; then
    echo "Restoring checked-in HISTORICAL_RECOVERY_ENABLED=false deployment..."
    CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --config wrangler.jsonc
  fi
  if [[ "${SECRET_SET}" -eq 1 ]]; then
    echo "Deleting temporary HISTORICAL_RECOVERY_CONTROL_TOKEN..."
    printf 'y\n' | CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh       secret delete HISTORICAL_RECOVERY_CONTROL_TOKEN
  fi
  rm -f "${TEMP_CONFIG}" "${BODY_FILE}" "${RESPONSE_FILE}"
  if [[ -n "${BASE_URL}" ]]; then
    code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST       "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
    echo "final local-evidence endpoint HTTP=${code} (expected 404)"
  fi
  echo "PB-04 safe close complete."
  exit "${status}"
}
trap safe_close EXIT INT TERM

[[ "${ENV_NAME}" == "live-canary" ]] || fail "CLOUDFLARE_ENV must be live-canary"
[[ -n "${BASE_URL}" ]] || fail "set ORDERSCOPE_LIVE_CANARY_URL to the live-canary Worker base URL"
[[ -f "${PACKET}" ]] || fail "missing remote execution packet: ${PACKET}"
[[ -f "${EVIDENCE}" ]] || fail "missing local evidence: ${EVIDENCE}"
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]]   || fail "run from l1-003-local-market-recovery"
git diff --quiet || fail "worktree has unstaged changes"
git diff --cached --quiet || fail "worktree has staged changes"

echo "== packet/evidence identity =="
PACKET="${PACKET}" EVIDENCE="${EVIDENCE}" node --input-type=module - <<'NODE'
import fs from "node:fs";
const packet = JSON.parse(fs.readFileSync(process.env.PACKET, "utf8"));
const evidenceText = fs.readFileSync(process.env.EVIDENCE, "utf8");
const evidence = JSON.parse(evidenceText);
if (packet.schemaVersion !== "l1-003-pb04-remote-execution-packet-v1"
  || packet.authorized !== false
  || packet.remoteMutationPerformed !== false
  || packet.environment !== "live-canary"
  || packet.coverageKey !== "NVDA|1Min|REGULAR|stock:iex:raw"
  || packet.frozenRemoteCheckpoint?.version !== 18
  || packet.frozenRemoteCheckpoint?.completeThrough !== "2026-09-08T20:00:00.000Z"
  || packet.source?.marketDate !== "2026-09-09"
  || packet.source?.contentSha256 !== evidence.contentSha256
  || evidence.contentSha256 !== "a0ac9c8aab46e9381982bb789c0c59463e536c6d19babf0457dff4dac13f86a2"
  || packet.recoveryId !== "L1-003-NVDA-20260909-LOCAL"
  || packet.chunks?.length !== 4) {
  throw new Error("Sep9 packet/evidence frozen identity mismatch");
}
fs.writeFileSync(process.env.BODY_FILE ?? ".pb04-local-evidence-body.json", JSON.stringify({
  sessionJson: evidenceText,
  calendarRevision: packet.session.calendarRevision,
}));
console.log(JSON.stringify({
  recoveryId: packet.recoveryId,
  evidenceHash: evidence.contentSha256,
  chunks: packet.chunks.map((c) => ({
    ordinal: c.ordinal, jobId: c.jobId, range: c.requestedRange,
    checkpointBefore: c.checkpointBefore, checkpointAfter: c.checkpointAfter,
    localProviderBars: c.localProviderBars, acknowledgedAbsent: c.acknowledgedAbsent,
  })),
}, null, 2));
NODE

echo
echo "== local acceptance before mutation =="
node --test --experimental-strip-types   src/local-history-evidence.test.ts   src/local-history-pb04.test.ts   src/local-history-pb04-simulation.test.ts   src/execution.test.ts
npm run typecheck
git diff --check

echo
echo "== health safe-baseline check =="
health="$(curl -fsS "${BASE_URL%/}/health")"
HEALTH="${health}" node --input-type=module - <<'NODE'
const h = JSON.parse(process.env.HEALTH);
if (h.mode !== "shadow" || h.news?.mode !== "disabled") {
  console.error(JSON.stringify(h, null, 2));
  throw new Error("live-canary is not in shadow/news-disabled safe baseline");
}
NODE
pre_code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk")"
[[ "${pre_code}" == "404" ]] || fail "historical local-evidence endpoint must be 404 before opening gate; got ${pre_code}"

echo
echo "== exact remote checkpoint preflight =="
preflight_sql="
SELECT CASE WHEN COUNT(*) = 1 THEN 1 ELSE 0 END AS preflight_ok
FROM coverage_checkpoint
WHERE coverage_key = '${COVERAGE_KEY}'
  AND symbol = 'NVDA'
  AND interval = '1Min'
  AND session_scope = 'REGULAR'
  AND logical_data_variant = 'stock:iex:raw'
  AND complete_through = '2026-09-08T20:00:00.000Z'
  AND state = 'COMPLETE'
  AND missing_ranges_json = '[]'
  AND universe_revision = 'stock-monitoring-canary-v0.1'
  AND version = 18
  AND blocker_json IS NULL
  AND retry_not_before IS NULL;
"
preflight_json="$(d1_json "${preflight_sql}")"
assert_single_json_value "${preflight_json}" "preflight_ok" "1"

attempt_sql="
SELECT COUNT(*) AS unresolved_attempts
FROM acquisition_attempt
WHERE coverage_key = '${COVERAGE_KEY}'
  AND finished_at IS NULL
  AND outcome IS NULL;
"
attempt_json="$(d1_json "${attempt_sql}")"
assert_single_json_value "${attempt_json}" "unresolved_attempts" "0"

echo
echo "== prepare temporary true-gate config =="
node --input-type=module - <<'NODE'
import fs from "node:fs";
const source = fs.readFileSync("wrangler.jsonc", "utf8");
const needle = '"HISTORICAL_RECOVERY_ENABLED": "false"';
const count = source.split(needle).length - 1;
if (count !== 2) throw new Error("expected exactly two checked-in false recovery gates");
fs.writeFileSync(".wrangler.pb04-live-canary.jsonc",
  source.replaceAll(needle, '"HISTORICAL_RECOVERY_ENABLED": "true"'));
NODE
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy   --dry-run --config "${TEMP_CONFIG}"

echo
echo "== create temporary control secret =="
TOKEN="$(openssl rand -hex 32)"
printf '%s' "${TOKEN}" | CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh   secret put HISTORICAL_RECOVERY_CONTROL_TOKEN
SECRET_SET=1

echo
echo "== deploy temporary recovery gate =="
CLOUDFLARE_ENV="${ENV_NAME}" bash scripts/run-wrangler-with-env.sh deploy --config "${TEMP_CONFIG}"
TEMP_GATE_DEPLOYED=1

gate_code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST   "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk")"
[[ "${gate_code}" == "401" ]] || fail "opened endpoint must reject missing token with 401; got ${gate_code}"

echo
echo "== execute frozen Sep9 four-chunk campaign =="
for ordinal in 1 2 3 4; do
  mapfile -t fields < <(
    PACKET="${PACKET}" ORDINAL="${ordinal}" node --input-type=module - <<'NODE'
import fs from "node:fs";
const p = JSON.parse(fs.readFileSync(process.env.PACKET, "utf8"));
const c = p.chunks.find((x) => x.ordinal === Number(process.env.ORDINAL));
if (!c) throw new Error("chunk not found");
console.log(p.recoveryId);
console.log(c.jobId);
console.log(c.requestedRange.startInclusive);
console.log(c.requestedRange.endExclusive);
console.log(c.localProviderBars);
console.log(c.acknowledgedAbsent);
console.log(c.checkpointBefore.version);
console.log(c.checkpointBefore.completeThrough);
console.log(c.checkpointAfter.version);
console.log(c.checkpointAfter.completeThrough);
NODE
  )
  recovery_id="${fields[0]}"
  job_id="${fields[1]}"
  range_start="${fields[2]}"
  range_end="${fields[3]}"
  provider_bars="${fields[4]}"
  acknowledged_absent="${fields[5]}"
  before_version="${fields[6]}"
  before_through="${fields[7]}"
  after_version="${fields[8]}"
  after_through="${fields[9]}"

  echo "-- chunk ${ordinal}: ${job_id} ${range_start} -> ${range_end}"
  curl -fsS -X POST     -H "authorization: Bearer ${TOKEN}"     -H "content-type: application/json"     -H "x-orderscope-recovery-id: ${recovery_id}"     -H "x-orderscope-job-id: ${job_id}"     -H "x-orderscope-checkpoint-version: ${before_version}"     -H "x-orderscope-complete-through: ${before_through}"     --data-binary "@${BODY_FILE}"     "${BASE_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk"     > "${RESPONSE_FILE}"

  RESPONSE_FILE="${RESPONSE_FILE}" JOB_ID="${job_id}" PROVIDER_BARS="${provider_bars}"   ABSENT="${acknowledged_absent}" AFTER_VERSION="${after_version}" AFTER_THROUGH="${after_through}"   node --input-type=module - <<'NODE'
import fs from "node:fs";
const r = JSON.parse(fs.readFileSync(process.env.RESPONSE_FILE, "utf8"));
if (r.accepted !== true
  || r.expectedJobId !== process.env.JOB_ID
  || r.result?.outcome !== "SUCCEEDED"
  || r.result?.summary?.outcome !== "SUCCEEDED"
  || r.result.summary.inserted + r.result.summary.matched !== Number(process.env.PROVIDER_BARS)
  || (r.result.summary.acknowledgedAbsent ?? 0) !== Number(process.env.ABSENT)
  || r.result.summary.conflicts !== 0
  || r.result.summary.rejected !== 0
  || r.result.summary.missing !== 0
  || r.checkpointAfter?.version !== Number(process.env.AFTER_VERSION)
  || r.checkpointAfter?.completeThrough !== process.env.AFTER_THROUGH
  || r.checkpointAfter?.state !== "COMPLETE"
  || r.checkpointAfter?.missingRanges?.length !== 0
  || r.stoppedAfterOneChunk !== true) {
  console.error(JSON.stringify(r, null, 2));
  throw new Error("chunk response verification failed");
}
console.log(JSON.stringify({
  accepted: r.accepted, jobId: r.expectedJobId,
  inserted: r.result.summary.inserted, matched: r.result.summary.matched,
  acknowledgedAbsent: r.result.summary.acknowledgedAbsent ?? 0,
  checkpointAfter: r.checkpointAfter,
  budget: r.budget,
}, null, 2));
NODE

  inspect_sql="
SELECT CASE WHEN
  (SELECT COUNT(*) FROM acquisition_attempt
    WHERE job_id = '${job_id}' AND outcome = 'SUCCEEDED') = 1
  AND (SELECT COUNT(*) FROM bar_acceptance_receipt
    WHERE job_id = '${job_id}') = ${provider_bars}
  AND (SELECT COUNT(*) FROM normalized_bar
    WHERE instrument_id = 'NVDA'
      AND interval = '1Min'
      AND session_kind = 'REGULAR'
      AND logical_data_variant = 'stock:iex:raw'
      AND bar_start_utc >= '${range_start}'
      AND bar_start_utc < '${range_end}') = ${provider_bars}
  AND (SELECT COALESCE(json_extract(diagnostic_json, '$.conflicts'), 0)
    FROM acquisition_attempt WHERE job_id = '${job_id}' AND outcome = 'SUCCEEDED' LIMIT 1) = 0
  AND (SELECT COALESCE(json_extract(diagnostic_json, '$.rejected'), 0)
    FROM acquisition_attempt WHERE job_id = '${job_id}' AND outcome = 'SUCCEEDED' LIMIT 1) = 0
  AND (SELECT COALESCE(json_extract(diagnostic_json, '$.missing'), 0)
    FROM acquisition_attempt WHERE job_id = '${job_id}' AND outcome = 'SUCCEEDED' LIMIT 1) = 0
  AND (SELECT version FROM coverage_checkpoint WHERE coverage_key = '${COVERAGE_KEY}') = ${after_version}
  AND (SELECT complete_through FROM coverage_checkpoint WHERE coverage_key = '${COVERAGE_KEY}') = '${after_through}'
  AND (SELECT state FROM coverage_checkpoint WHERE coverage_key = '${COVERAGE_KEY}') = 'COMPLETE'
  AND (SELECT missing_ranges_json FROM coverage_checkpoint WHERE coverage_key = '${COVERAGE_KEY}') = '[]'
  AND (SELECT blocker_json FROM coverage_checkpoint WHERE coverage_key = '${COVERAGE_KEY}') IS NULL
THEN 1 ELSE 0 END AS inspection_ok;
"
  inspect_json="$(d1_json "${inspect_sql}")"
  assert_single_json_value "${inspect_json}" "inspection_ok" "1"
  echo "chunk ${ordinal}: persisted evidence PASS"
done

echo
echo "== final Sep9 checkpoint =="
final_sql="
SELECT CASE WHEN COUNT(*) = 1 THEN 1 ELSE 0 END AS final_ok
FROM coverage_checkpoint
WHERE coverage_key = '${COVERAGE_KEY}'
  AND version = 22
  AND complete_through = '2026-09-09T20:00:00.000Z'
  AND state = 'COMPLETE'
  AND missing_ranges_json = '[]'
  AND blocker_json IS NULL;
"
final_json="$(d1_json "${final_sql}")"
assert_single_json_value "${final_json}" "final_ok" "1"

echo "PB-04 Sep9 campaign: ACCEPTED REMOTELY at v22 / 2026-09-09T20:00:00.000Z"
echo "Safe-close will now restore the false gate and delete the temporary secret."
