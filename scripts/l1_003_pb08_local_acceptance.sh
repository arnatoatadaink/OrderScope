#!/usr/bin/env bash
set -euo pipefail

[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || {
  echo "ERROR: run from l1-003-local-market-recovery" >&2
  exit 1
}
git diff --quiet || { echo "ERROR: worktree has unstaged changes" >&2; exit 1; }
git diff --cached --quiet || { echo "ERROR: worktree has staged changes" >&2; exit 1; }

echo "== PB-08 entry-packet local acceptance =="
node --test --experimental-strip-types   src/pb08-frontier-catchup.test.ts   src/pb08-frontier-order.test.ts   src/pb07-stability.test.ts   src/pb07-opportunity-order.test.ts   src/schedule.test.ts   src/job-priority.test.ts   src/execution.test.ts

npm run typecheck
bash -n scripts/l1_003_pb08_entry_packet_preflight.sh
git diff --check

echo
echo "PB-08 local acceptance: PASS"
echo "snapshot frontier target: 2026-09-24T20:00:00.000Z"
echo "NVDA catch-up jobs: 4"
echo "remoteMutation=false"
