#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <start-utc> <end-utc>" >&2
  echo "example: $0 2026-09-11T13:30:00Z 2026-09-11T13:35:00Z" >&2
  exit 2
fi
START="$1"
END="$2"

case "$START$END" in
  *"'"*|*";"*) echo "timestamps contain forbidden SQL characters" >&2; exit 2;;
esac

DB=STATE_DB
ENV=live-canary

echo '== git =='
git status --short
git rev-parse HEAD

echo '== local adapter tests =='
PYTHONPATH=analysis/app uv run pytest -q \
  analysis/tests/storage/test_d1_custody.py \
  analysis/tests/storage/test_d1_bounded_export.py \
  analysis/tests/storage/test_d1_remote_export.py

echo '== D1 target =='
npx wrangler d1 info "$DB" --env "$ENV"

echo '== read-only bounded candidate summary =='
SQL="SELECT COUNT(*) AS row_count, MIN(bar_start_utc) AS first_bar_start_utc, MAX(bar_start_utc) AS last_bar_start_utc FROM normalized_bar WHERE bar_start_utc >= '$START' AND bar_start_utc < '$END';"
npx wrangler d1 execute "$DB" --remote --env "$ENV" --command "$SQL"

echo '== control path =='
npx wrangler d1 execute "$DB" --remote --env "$ENV" --command 'SELECT 1 AS control_path_ok;'

echo '== deployed health =='
curl -fsS http://orderscope-market-worker-live-canary.yuihout2.workers.dev/health
printf '\n'

echo 'READ-ONLY R0-007 PREFLIGHT COMPLETE.'
echo 'No row export, Worker mutation, D1 write, purge, migration, or feature activation is performed.'
