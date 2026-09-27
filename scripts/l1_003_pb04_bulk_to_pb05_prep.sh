#!/usr/bin/env bash
set -euo pipefail

MANIFEST="${PB04_BULK_MANIFEST:-scripts/l1_003_pb04_bulk_manifest.json}"

[[ -f "${MANIFEST}" ]] || { echo "missing manifest: ${MANIFEST}" >&2; exit 1; }
[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || {
  echo "run from l1-003-local-market-recovery" >&2; exit 1;
}
git diff --quiet || { echo "worktree has unstaged changes" >&2; exit 1; }
git diff --cached --quiet || { echo "worktree has staged changes" >&2; exit 1; }

mapfile -t sessions < <(MANIFEST="${MANIFEST}" node --input-type=module - <<'NODE'
import fs from "node:fs";
const m = JSON.parse(fs.readFileSync(process.env.MANIFEST, "utf8"));
if (m.schemaVersion !== "l1-003-pb04-bulk-manifest-v1") throw new Error("unsupported manifest");
for (const s of m.sessions) console.log(s.marketDate);
NODE
)

echo "PB-04 bulk closeout driver"
echo "sessions=${sessions[*]}"
echo "This driver preserves one-session child windows and safe-close after every session."

for session in "${sessions[@]}"; do
  echo
  echo "============================================================"
  echo "PB-04 child session ${session}"
  echo "============================================================"
  PB04_SESSION="${session}" PB04_BULK_MANIFEST="${MANIFEST}"     bash scripts/l1_003_pb04_bulk_child_window.sh

  echo
  echo "== post-child safe-baseline assertion: ${session} =="
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST     "${ORDERSCOPE_LIVE_CANARY_URL%/}/control/historical-recovery/nvda/local-evidence-next-chunk" || true)"
  [[ "${code}" == "404" ]] || {
    echo "ERROR: child ${session} did not return to closed endpoint; HTTP=${code}" >&2
    exit 1
  }
done

echo
echo "PB-04 bounded bulk campaign children completed."
echo "No PB-06 scheduler activation has been performed."
echo "Run scripts/l1_003_pb05_readonly_assessment.sh next."
