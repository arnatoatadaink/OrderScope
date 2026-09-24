#!/usr/bin/env bash
set -euo pipefail

[[ "$(git branch --show-current)" == "l1-003-local-market-recovery" ]] || {
  echo "ERROR: run from l1-003-local-market-recovery" >&2
  exit 1
}
git diff --quiet || { echo "ERROR: worktree has unstaged changes" >&2; exit 1; }
git diff --cached --quiet || { echo "ERROR: worktree has staged changes" >&2; exit 1; }

echo "== PB-06 scheduler handoff local acceptance =="
node --test --experimental-strip-types   src/pb06-handoff.test.ts   src/schedule.test.ts   src/job-priority.test.ts   src/execution.test.ts

npm run typecheck
git diff --check

echo
echo "PB-06 local acceptance: PASS"
echo "normal scheduler execution uses prioritized single-instrument jobs"
echo "maxJobsPerTick remains unchanged"
echo "retention remains unchanged"
echo "Universe remains unchanged"
echo "Cron remains unchanged"
echo "remoteMutation=false"
