#!/usr/bin/env bash
set -euo pipefail

[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || {
  echo "ERROR: run from l1-003-local-market-recovery" >&2
  exit 1
}
git diff --quiet || { echo "ERROR: worktree has unstaged changes" >&2; exit 1; }
git diff --cached --quiet || { echo "ERROR: worktree has staged changes" >&2; exit 1; }

echo "== PB-07 stability local acceptance =="
node --test --experimental-strip-types   src/pb07-stability.test.ts   src/pb06-handoff.test.ts   src/schedule.test.ts   src/job-priority.test.ts   src/execution.test.ts

npm run typecheck
bash -n scripts/l1_003_pb07_readonly_preflight.sh
git diff --check

echo
echo "PB-07 local acceptance: PASS"
echo "expected NVDA progression: v59 -> v60 -> v61"
echo "range1: 2026-09-23T15:09:00.000Z -> 2026-09-23T16:49:00.000Z"
echo "range2: 2026-09-23T16:48:00.000Z -> 2026-09-23T18:28:00.000Z"
echo "remoteMutation=false"
