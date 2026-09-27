#!/usr/bin/env bash
set -Eeuo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "ERROR: run inside OrderScope checkout" >&2; exit 2; }
cd "$REPO_ROOT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
EVIDENCE_ROOT="${HOME}/data/orderscope/mig09e/${STAMP}"
mkdir -p "$EVIDENCE_ROOT"
LOG="$EVIDENCE_ROOT/acceptance.log"
SUMMARY="$EVIDENCE_ROOT/summary.tsv"
API_LOG="$EVIDENCE_ROOT/local-api.log"
exec > >(tee -a "$LOG") 2>&1
printf "check\tresult\tdetail\n" > "$SUMMARY"

record() { printf "%s\t%s\t%s\n" "$1" "$2" "$3" >> "$SUMMARY"; printf "[%s] %s: %s\n" "$2" "$1" "$3"; }
fail() { record "$1" FAIL "$2"; exit 1; }

API_PID=""
cleanup() {
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'rc=$?; echo "MIG-09E interrupted: exit=$rc"; echo "Evidence: $EVIDENCE_ROOT"; exit "$rc"' ERR

echo "=== MIG-09E final acceptance ==="
echo "timestamp_utc=$STAMP"
echo "repo_root=$REPO_ROOT"
echo "branch=$(git branch --show-current)"
echo "head=$(git rev-parse HEAD)"

case "$REPO_ROOT" in /mnt/c/*|/mnt/C/*) record canonical_source_path PASS "$REPO_ROOT" ;; *) fail canonical_source_path "expected /mnt/c source" ;; esac
[[ -z "$(git status --porcelain)" ]] || { git status --short --branch; fail clean_worktree "working tree is not clean"; }
record clean_worktree PASS "clean before acceptance"

echo "=== runtime ==="
if [[ -s "${HOME}/.nvm/nvm.sh" ]]; then . "${HOME}/.nvm/nvm.sh"; nvm use; fi
NODE_VERSION="$(node --version)"
[[ "$NODE_VERSION" == "v24.21.0" ]] || fail node_version "expected v24.21.0, got $NODE_VERSION"
[[ "$(node -p 'process.platform')" == "linux" ]] || fail node_platform "Node is not Linux"
record node_version PASS "$NODE_VERSION"
record node_platform PASS linux
uv --version

echo "=== migration snapshot hash ==="
if sha256sum --check MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256; then record migration_snapshot_hash PASS "all entries OK"; else fail migration_snapshot_hash "sha256 verification failed"; fi

echo "=== Python lock/env ==="
uv lock --check
record uv_lock_check PASS "uv.lock current"
bash scripts/run-local-wsl.sh sync
record python_sync PASS "wrapper sync completed"
PYTHON_INFO="$(bash scripts/run-local-wsl.sh python -c 'import sys; print(sys.version.split()[0]); print(sys.executable); print(sys.prefix)')"
printf "%s\n" "$PYTHON_INFO"
PYTHON_VERSION="$(printf "%s\n" "$PYTHON_INFO" | sed -n '1p')"
PYTHON_EXE="$(printf "%s\n" "$PYTHON_INFO" | sed -n '2p')"
PYTHON_PREFIX="$(printf "%s\n" "$PYTHON_INFO" | sed -n '3p')"
[[ "$PYTHON_VERSION" == 3.13.* ]] || fail python_version "expected 3.13.x, got $PYTHON_VERSION"
[[ "$PYTHON_PREFIX" == "${HOME}/.local/share/orderscope/venv" ]] || fail python_env_path "unexpected prefix $PYTHON_PREFIX"
PYTHON_FS="$(findmnt -T "$PYTHON_PREFIX" -no FSTYPE 2>/dev/null || true)"
case "$PYTHON_FS" in 9p|drvfs|ntfs|fuseblk|"") fail python_env_filesystem "unexpected filesystem $PYTHON_FS" ;; *) record python_env_filesystem PASS "$PYTHON_FS" ;; esac
record python_version PASS "$PYTHON_VERSION"
record python_env_path PASS "$PYTHON_EXE"

echo "=== Node dependencies/tests ==="
npm ci
record npm_ci PASS "completed without EIO"
npm test
record node_tests PASS "npm test completed"
npm run typecheck
record typecheck PASS "tsc completed"

echo "=== Python tests ==="
bash scripts/run-local-wsl.sh pytest -q
record python_tests PASS "pytest completed"

echo "=== Wrangler dry-run ==="
npm run deploy:check -- --env live-canary
record wrangler_dry_run PASS "live-canary dry-run completed"

echo "=== Local API ==="
if ss -ltn 2>/dev/null | grep -qE '127[.]0[.]0[.]1:8000|0[.]0[.]0[.]0:8000|\[::\]:8000'; then fail local_api_precondition "port 8000 already in use"; fi
bash scripts/run-local-wsl.sh api --port 8000 >"$API_LOG" 2>&1 &
API_PID=$!
HEALTH_OK=0
for _ in $(seq 1 30); do
  if curl --fail --silent --show-error http://127.0.0.1:8000/health >"$EVIDENCE_ROOT/health.json" 2>>"$API_LOG"; then HEALTH_OK=1; break; fi
  kill -0 "$API_PID" 2>/dev/null || break
  sleep 1
done
[[ "$HEALTH_OK" -eq 1 ]] || fail local_api_health "health failed; see $API_LOG"
if ss -ltn 2>/dev/null | grep -qE '127[.]0[.]0[.]1:8000'; then record local_api_bind PASS "127.0.0.1:8000"; else fail local_api_bind "loopback listener not confirmed"; fi
record local_api_health PASS "HTTP 200 /health"
kill "$API_PID" 2>/dev/null || true
wait "$API_PID" 2>/dev/null || true
API_PID=""

echo "=== Git/security boundary ==="
FORBIDDEN="$(git ls-files -- .env .env.cloudflare .dev.vars node_modules .venv __pycache__ var .wrangler || true)"
[[ -z "$FORBIDDEN" ]] || { printf "%s\n" "$FORBIDDEN"; fail forbidden_tracked_files "runtime/secret/cache path tracked"; }
record forbidden_tracked_files PASS none
git check-ignore -q .env && git check-ignore -q .env.cloudflare || fail dotenv_ignore "dotenv ignore incomplete"
record dotenv_ignore PASS ".env and .env.cloudflare ignored"
[[ -z "$(git status --porcelain)" ]] || { git status --short --branch; fail final_clean_worktree "tracked changes appeared"; }
record final_clean_worktree PASS clean
git diff --check
record git_diff_check PASS "no whitespace errors"

echo "=== summary ==="
column -t -s $'\t' "$SUMMARY" 2>/dev/null || cat "$SUMMARY"
echo "MIG-09E local acceptance completed successfully."
echo "Evidence directory: $EVIDENCE_ROOT"
echo "Return summary.tsv and acceptance.log; include local-api.log only on API failure."
