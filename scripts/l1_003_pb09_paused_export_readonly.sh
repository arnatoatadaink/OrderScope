#!/usr/bin/env bash
set -euo pipefail
# Execute inside a separately authorized pause; this helper itself only reads.
OUTPUT="${1:?output directory required}"
mkdir -p "${OUTPUT}"
for observation in 1 2; do
  CLOUDFLARE_ENV=live-canary bash scripts/run-wrangler-with-env.sh d1 execute orderscope-state-live-canary --remote --json --command="SELECT * FROM normalized_bar WHERE bar_start_utc >= '2026-09-01T16:03:00.000Z' AND bar_start_utc < '2026-09-01T16:04:00.000Z' ORDER BY bar_start_utc, identity_key LIMIT 2;" > "${OUTPUT}/export-read-${observation}.json"
done
python3 scripts/l1_003_pb09_export_receipt.py "${OUTPUT}/export-read-1.json" "${OUTPUT}/export-read-2.json"
