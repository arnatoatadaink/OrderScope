#!/usr/bin/env bash
set -euo pipefail

# R0-007 first real bounded custody transfer.
# Remote side is strictly read-only: two identical SELECTs against one fixed,
# historical, one-minute window. Artifacts are written only beneath ignored
# local var/ storage. No D1 write, purge, Worker deploy, Cron mutation, or
# feature activation occurs here.

ENV_NAME="live-canary"
DB_BINDING="STATE_DB"
SOURCE_DATABASE_ID="03c85865-1aa3-4b0c-b219-18987cd260a6"
SOURCE_ENVIRONMENT="live-canary"
TABLE_NAME="normalized_bar"
WINDOW_START="2026-09-01T16:03:00+00:00"
WINDOW_END="2026-09-01T16:04:00+00:00"
QUERY_START="2026-09-01T16:03:00.000Z"
QUERY_END="2026-09-01T16:04:00.000Z"
MAX_ROWS=20
EXPECTED_ROWS=1

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
SOURCE_REVISION="$(git rev-parse HEAD)"

OUT_ROOT="var/d1-custody/r0-007-first-remote"
ARTIFACT_REL="r0-007-first-remote/normalized_bar_20260901T160300Z_20260901T160400Z.ndjson"
ARTIFACT_PATH="var/d1-custody/${ARTIFACT_REL}"
EXPORT_MANIFEST_PATH="${OUT_ROOT}/export-manifest.json"
CUSTODY_MANIFEST_PATH="${OUT_ROOT}/custody-manifest.json"
TMP1="${OUT_ROOT}/wrangler-pass-1.json"
TMP2="${OUT_ROOT}/wrangler-pass-2.json"
mkdir -p "$OUT_ROOT"

SQL="SELECT * FROM normalized_bar WHERE bar_start_utc >= '${QUERY_START}' AND bar_start_utc < '${QUERY_END}' ORDER BY bar_start_utc, identity_key LIMIT $((MAX_ROWS + 1));"

echo "== local acceptance =="
PYTHONPATH=analysis/app uv run pytest -q \
  analysis/tests/storage/test_d1_remote_export.py \
  analysis/tests/storage/test_d1_bounded_export.py \
  analysis/tests/storage/test_d1_custody.py

echo "== D1 target =="
npx wrangler d1 info orderscope-state-live-canary --env "$ENV_NAME"

echo "== remote SELECT pass 1 =="
npx wrangler d1 execute "$DB_BINDING" \
  --env "$ENV_NAME" \
  --remote \
  --json \
  --command "$SQL" > "$TMP1"

echo "== remote SELECT pass 2 =="
npx wrangler d1 execute "$DB_BINDING" \
  --env "$ENV_NAME" \
  --remote \
  --json \
  --command "$SQL" > "$TMP2"

echo "== canonicalize / verify custody =="
PYTHONPATH=analysis/app uv run python - "$TMP1" "$TMP2" "$ARTIFACT_PATH" "$EXPORT_MANIFEST_PATH" "$CUSTODY_MANIFEST_PATH" "$SOURCE_REVISION" <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from orderscope_local.storage.d1_remote_export import canonicalize_wrangler_json

p1, p2, artifact_path, export_path, custody_path, source_revision = map(Path, sys.argv[1:6]) + [None]  # type: ignore
PY
