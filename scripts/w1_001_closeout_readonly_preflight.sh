#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="live-canary"
DB_NAME="orderscope-state-live-canary"
BRANCH="docs/mermaid-conventions-v0.1"

printf '\n== git / local acceptance ==\n'
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
git status --short
git rev-parse HEAD

npm test
npm run typecheck
npm run cf-typegen
npm run deploy:check -- --env "$ENV_NAME"
git diff --check

if [[ -n "$(git status --short)" ]]; then
  echo "ERROR: working tree is not clean after preflight" >&2
  exit 1
fi

printf '\n== Cloudflare read-only control path ==\n'
npx wrangler whoami
npx wrangler d1 info "$DB_NAME" --env "$ENV_NAME"
npx wrangler d1 execute STATE_DB --env "$ENV_NAME" --remote --command "SELECT 1 AS control_path_ok"
npx wrangler d1 execute STATE_DB --env "$ENV_NAME" --remote --command "PRAGMA table_list"
npx wrangler deployments list --env "$ENV_NAME"

cat <<'EOF'

READ-ONLY PREFLIGHT COMPLETE.

No Worker deployment, Cron mutation, D1 write, News activation, migration, export,
or purge is performed by this script.

Before any live mutation, verify the deployed /health endpoint reports:
  WORKER_MODE=shadow
  NEWS_ACQUISITION_ENABLED=false
  UNIVERSE_PROFILE=canary-v0.1
  NEWS_ACQUISITION_CADENCE_MINUTES=5
  NEWS_ACQUISITION_CANARY_SYMBOLS=AMD,NVDA
  Cron=* * * * *

If any auth/7403/quota/binding/config drift appears, do not open the change window.
EOF
