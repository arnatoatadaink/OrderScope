#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_BASE="${ORDERSCOPE_DATA_BASE:-${HOME}/data/orderscope}"
DATA_ROOT="${ORDERSCOPE_DATA_ROOT:-${DATA_BASE}/local}"
WRANGLER_PERSIST_TO="${ORDERSCOPE_WRANGLER_PERSIST_TO:-${DATA_BASE}/wrangler-state}"

if [[ "${DATA_BASE}" != /* || "${DATA_ROOT}" != /* || "${WRANGLER_PERSIST_TO}" != /* ]]; then
  echo "OrderScope local paths must be absolute WSL paths" >&2
  exit 2
fi

repo_real="$(realpath "${REPO_ROOT}")"
data_root_real="$(realpath -m "${DATA_ROOT}")"
wrangler_state_real="$(realpath -m "${WRANGLER_PERSIST_TO}")"

if [[ "${data_root_real}" == "${repo_real}"/* || "${wrangler_state_real}" == "${repo_real}"/* ]]; then
  echo "OrderScope mutable data must not be inside the source checkout" >&2
  exit 2
fi

mkdir -p "${DATA_ROOT}" "${WRANGLER_PERSIST_TO}"

for path in "${DATA_ROOT}" "${WRANGLER_PERSIST_TO}"; do
  filesystem="$(findmnt -T "${path}" -no FSTYPE 2>/dev/null || true)"
  case "${filesystem}" in
    9p|drvfs|ntfs|fuseblk)
      echo "OrderScope mutable data must be on WSL native filesystem: ${path} (${filesystem})" >&2
      exit 2
      ;;
  esac
done

export ORDERSCOPE_DATA_ROOT="${DATA_ROOT}"
export ORDERSCOPE_WRANGLER_PERSIST_TO="${WRANGLER_PERSIST_TO}"
cd "${REPO_ROOT}"

use_wsl_node() {
  if [[ -s "${HOME}/.nvm/nvm.sh" ]]; then
    # nvm use reads this checkout's .nvmrc, so npm/npx cannot fall through to
    # a Windows-native Node installation when the wrapper is called directly.
    # shellcheck disable=SC1091
    . "${HOME}/.nvm/nvm.sh"
    nvm use --silent >/dev/null
  fi
  if ! command -v node >/dev/null 2>&1 || [[ "$(node -p 'process.platform')" != "linux" ]]; then
    echo "OrderScope local Wrangler requires a WSL/Linux Node.js runtime" >&2
    exit 2
  fi
}

usage() {
  cat >&2 <<'EOF'
Usage:
  bash scripts/run-local-wsl.sh env
  bash scripts/run-local-wsl.sh api [--port PORT]
  bash scripts/run-local-wsl.sh python SCRIPT [ARGS...]
  bash scripts/run-local-wsl.sh pytest [ARGS...]
  bash scripts/run-local-wsl.sh wrangler [ARGS...]

The wrangler command always runs local persistence under
$ORDERSCOPE_WRANGLER_PERSIST_TO. Python commands receive
$ORDERSCOPE_DATA_ROOT.
EOF
}

command_name="${1:-}"
shift || true

case "${command_name}" in
  env)
    printf 'REPO_ROOT=%s\n' "${REPO_ROOT}"
    printf 'ORDERSCOPE_DATA_ROOT=%s\n' "${ORDERSCOPE_DATA_ROOT}"
    printf 'ORDERSCOPE_WRANGLER_PERSIST_TO=%s\n' "${ORDERSCOPE_WRANGLER_PERSIST_TO}"
    ;;
  api)
    export PYTHONPATH="${REPO_ROOT}/analysis/app${PYTHONPATH:+:${PYTHONPATH}}"
    exec uv run python -m orderscope_local.cli serve "$@"
    ;;
  python)
    if [[ "$#" -eq 0 ]]; then
      usage
      exit 2
    fi
    export PYTHONPATH="${REPO_ROOT}/analysis/app${PYTHONPATH:+:${PYTHONPATH}}"
    exec uv run python "$@"
    ;;
  pytest)
    exec uv run pytest "$@"
    ;;
  wrangler)
    use_wsl_node
    exec npx wrangler dev --local --persist-to "${ORDERSCOPE_WRANGLER_PERSIST_TO}" "$@"
    ;;
  *)
    usage
    exit 2
    ;;
esac
