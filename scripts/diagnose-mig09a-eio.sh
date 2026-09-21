#!/usr/bin/env bash
set -uo pipefail

# MIG-09A: /mnt/c EIO diagnostic probe
# Safe-by-default: does not modify the repository's node_modules or .venv.
# It writes only to temporary probe directories outside the repository.
#
# Usage:
#   bash scripts/diagnose-mig09a-eio.sh
#   bash scripts/diagnose-mig09a-eio.sh --heavy
#
# --heavy additionally runs npm ci in isolated /mnt/c and WSL-native temp dirs.

HEAVY=0
if [[ "${1:-}" == "--heavy" ]]; then
  HEAVY=1
elif [[ -n "${1:-}" ]]; then
  echo "usage: $0 [--heavy]" >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "ERROR: run this inside the OrderScope git checkout" >&2
  exit 2
}
cd "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_BASE="${HOME}/data/orderscope/mig09a"
LOG_DIR="${LOG_BASE}/${STAMP}"
mkdir -p "$LOG_DIR"
LOG="${LOG_DIR}/diagnostic.log"
SUMMARY="${LOG_DIR}/summary.tsv"

exec > >(tee -a "$LOG") 2>&1

printf 'check\tresult\tdetail\n' > "$SUMMARY"

record() {
  local check="$1" result="$2" detail="$3"
  printf '%s\t%s\t%s\n' "$check" "$result" "$detail" >> "$SUMMARY"
  printf '[%s] %s: %s\n' "$result" "$check" "$detail"
}

run_capture() {
  local name="$1"
  shift
  local out="${LOG_DIR}/${name}.out"
  if "$@" >"$out" 2>&1; then
    record "$name" PASS "exit=0; log=$out"
    return 0
  else
    local rc=$?
    if grep -Eqi 'EIO|Input/output error|i/o error|os error 5' "$out"; then
      record "$name" EIO "exit=$rc; log=$out"
    else
      record "$name" FAIL "exit=$rc; log=$out"
    fi
    return "$rc"
  fi
}

echo "=== MIG-09A diagnostic ==="
echo "timestamp_utc=$STAMP"
echo "root=$ROOT"
echo "kernel=$(uname -r)"
echo "wsl_distro=${WSL_DISTRO_NAME:-unknown}"
echo "node=$(node --version 2>/dev/null || echo unavailable)"
echo "npm=$(npm --version 2>/dev/null || echo unavailable)"
echo "uv=$(uv --version 2>/dev/null || echo unavailable)"
git status --short --branch || true
mount | grep -E ' on /mnt/c ' || true
df -T "$ROOT" "$HOME" || true

case "$ROOT" in
  /mnt/c/*|/mnt/C/*) record source_on_mntc PASS "$ROOT" ;;
  *) record source_on_mntc FAIL "expected Windows source under /mnt/c, got $ROOT" ;;
esac

for f in package.json package-lock.json uv.toml .git/HEAD; do
  if [[ -r "$f" ]]; then
    record "readable:$f" PASS "readable"
  else
    record "readable:$f" FAIL "not readable"
  fi
done

echo "=== repeated source reads ==="
READ_OUT="${LOG_DIR}/repeated-read.out"
: > "$READ_OUT"
read_failed=0
for i in $(seq 1 250); do
  for f in package.json package-lock.json uv.toml .git/HEAD; do
    if ! sha256sum "$f" >>"$READ_OUT" 2>&1; then
      echo "iteration=$i file=$f" >>"$READ_OUT"
      read_failed=1
      break 2
    fi
  done
done
if [[ "$read_failed" -eq 0 ]]; then
  record repeated_source_read PASS "250 iterations x 4 files"
elif grep -Eqi 'EIO|Input/output error|i/o error|os error 5' "$READ_OUT"; then
  record repeated_source_read EIO "see $READ_OUT"
else
  record repeated_source_read FAIL "see $READ_OUT"
fi

MNTC_PARENT="$(dirname "$ROOT")"
MNTC_TMP="${MNTC_PARENT}/.orderscope-mig09a-probe-${STAMP}"
WSL_TMP="${HOME}/.cache/orderscope-mig09a-probe-${STAMP}"

cleanup() {
  rm -rf "$MNTC_TMP" "$WSL_TMP" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "$MNTC_TMP" "$WSL_TMP"

small_io_probe() {
  local dir="$1"
  local out="$2"
  : > "$out"
  local i f
  for i in $(seq 1 2000); do
    f="$dir/f-$i"
    printf 'orderscope-mig09a-%08d\n' "$i" > "$f" 2>>"$out" || return 1
    cat "$f" >/dev/null 2>>"$out" || return 1
  done
  find "$dir" -maxdepth 1 -type f -name 'f-*' -delete >>"$out" 2>&1 || return 1
}

echo "=== small create/read/delete comparison ==="
if small_io_probe "$MNTC_TMP" "${LOG_DIR}/small-io-mntc.out"; then
  record small_io_mntc PASS "2000 files"
else
  if grep -Eqi 'EIO|Input/output error|i/o error|os error 5' "${LOG_DIR}/small-io-mntc.out"; then
    record small_io_mntc EIO "see small-io-mntc.out"
  else
    record small_io_mntc FAIL "see small-io-mntc.out"
  fi
fi

if small_io_probe "$WSL_TMP" "${LOG_DIR}/small-io-wsl.out"; then
  record small_io_wsl PASS "2000 files"
else
  if grep -Eqi 'EIO|Input/output error|i/o error|os error 5' "${LOG_DIR}/small-io-wsl.out"; then
    record small_io_wsl EIO "see small-io-wsl.out"
  else
    record small_io_wsl FAIL "see small-io-wsl.out"
  fi
fi

if [[ "$HEAVY" -eq 1 ]]; then
  echo "=== isolated npm ci comparison ==="

  for d in "$MNTC_TMP/npm" "$WSL_TMP/npm"; do
    mkdir -p "$d"
    cp package.json package-lock.json "$d/"
  done

  run_capture npm_ci_mntc bash -lc "cd '$MNTC_TMP/npm' && npm ci"
  run_capture npm_ci_wsl  bash -lc "cd '$WSL_TMP/npm' && npm ci"

  echo "=== post-heavy source reads ==="
  POST_OUT="${LOG_DIR}/post-heavy-read.out"
  : > "$POST_OUT"
  post_failed=0
  for i in $(seq 1 100); do
    for f in package.json uv.toml .git/HEAD; do
      if ! sha256sum "$f" >>"$POST_OUT" 2>&1; then
        echo "iteration=$i file=$f" >>"$POST_OUT"
        post_failed=1
        break 2
      fi
    done
  done
  if [[ "$post_failed" -eq 0 ]]; then
    record post_heavy_source_read PASS "100 iterations x 3 files"
  elif grep -Eqi 'EIO|Input/output error|i/o error|os error 5' "$POST_OUT"; then
    record post_heavy_source_read EIO "see $POST_OUT"
  else
    record post_heavy_source_read FAIL "see $POST_OUT"
  fi
else
  record npm_ci_comparison SKIP "rerun with --heavy"
fi

echo
echo "=== summary ==="
column -t -s $'\t' "$SUMMARY" 2>/dev/null || cat "$SUMMARY"
echo
echo "Artifacts: $LOG_DIR"
echo "Return the summary.tsv and diagnostic.log contents for review."
