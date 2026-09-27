#!/usr/bin/env bash
set -euo pipefail

MANIFEST="${PB04_BULK_MANIFEST:-scripts/l1_003_pb04_bulk_manifest.json}"
INPUT_DIR="${PB04_INPUT_DIR:-var/l1-003/local-market-recovery/nvda}"

[[ -f "${MANIFEST}" ]] || { echo "missing manifest: ${MANIFEST}" >&2; exit 1; }

mapfile -t rows < <(MANIFEST="${MANIFEST}" node --input-type=module - <<'NODE'
import fs from "node:fs";
const m = JSON.parse(fs.readFileSync(process.env.MANIFEST, "utf8"));
if (m.schemaVersion !== "l1-003-pb04-bulk-manifest-v1") throw new Error("unsupported manifest");
for (const s of m.sessions) {
  console.log([s.marketDate,s.entryVersion,s.entryThrough].join("|"));
}
NODE
)

for row in "${rows[@]}"; do
  IFS='|' read -r session entry_version entry_through <<<"${row}"
  dry="${INPUT_DIR}/PB04_NVDA_${session}_DRYRUN.json"
  remote="${INPUT_DIR}/PB04_NVDA_${session}_REMOTE_PACKET.json"
  echo "== prepare ${session} =="
  node --experimental-strip-types scripts/l1_003_pb04_local_dry_run.ts     --session "${session}"     --checkpoint-version "${entry_version}"     --checkpoint-through "${entry_through}"     --output "${dry}"
  node --experimental-strip-types scripts/l1_003_pb04_remote_execution_packet.ts     --dry-run "${dry}"     --remote-checkpoint-version "${entry_version}"     --remote-checkpoint-through "${entry_through}"     --output "${remote}"
done

echo
echo "== verify frozen packet identities =="
MANIFEST="${MANIFEST}" INPUT_DIR="${INPUT_DIR}" node --input-type=module - <<'NODE'
import fs from "node:fs";
const m = JSON.parse(fs.readFileSync(process.env.MANIFEST, "utf8"));
for (const s of m.sessions) {
  const p = JSON.parse(fs.readFileSync(`${process.env.INPUT_DIR}/PB04_NVDA_${s.marketDate}_REMOTE_PACKET.json`, "utf8"));
  if (p.schemaVersion !== "l1-003-pb04-remote-execution-packet-v1"
    || p.authorized !== false || p.remoteMutationPerformed !== false
    || p.source?.marketDate !== s.marketDate
    || p.source?.contentSha256 !== s.evidenceSha256
    || p.frozenRemoteCheckpoint?.version !== s.entryVersion
    || p.frozenRemoteCheckpoint?.completeThrough !== s.entryThrough
    || p.chunks?.length !== 4
    || JSON.stringify(p.chunks.map((c) => c.jobId)) !== JSON.stringify(s.jobIds)
    || p.chunks.at(-1)?.checkpointAfter?.version !== s.exitVersion
    || p.chunks.at(-1)?.checkpointAfter?.completeThrough !== s.exitThrough
    || p.chunks.reduce((n,c)=>n+c.expectedGridBars,0) !== 390
    || p.chunks.reduce((n,c)=>n+c.acknowledgedAbsent,0) !== 0) {
    throw new Error(`bulk packet identity mismatch: ${s.marketDate}`);
  }
  console.log(`${s.marketDate}: PASS v${s.entryVersion}->v${s.exitVersion} 390 bars absence=0`);
}
NODE

echo
node --test --experimental-strip-types   src/local-history-evidence.test.ts   src/local-history-pb04.test.ts   src/local-history-pb04-simulation.test.ts   src/execution.test.ts
npm run typecheck
git diff --check

echo "PB-04 bulk closeout preparation: PASS / remoteMutation=false"
