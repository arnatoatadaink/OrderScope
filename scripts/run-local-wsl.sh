#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_BASE="${ORDERSCOPE_DATA_BASE:-${HOME}/data/orderscope}"
DATA_ROOT="${ORDERSCOPE_DATA_ROOT:-${DATA_BASE}/local}"
WRANGLER_PERSIST_TO="${ORDERSCOPE_WRANGLER_PERSIST_TO:-${DATA_BASE}/wrangler-state}"
PYTHON_ENV="${ORDERSCOPE_PYTHON_ENV:-${HOME}/.local/share/orderscope/venv}"

if [[ "${DATA_BASE}" != /* || "${DATA_ROOT}" != /* || "${WRANGLER_PERSIST_TO}" != /* || "${PYTHON_ENV}" != /* ]]; then
  echo "OrderScope local paths must be absolute WSL paths" >&2
  exit 2
fi

repo_real="$(realpath "${REPO_ROOT}")"
data_root_real="$(realpath -m "${DATA_ROOT}")"
wrangler_state_real="$(realpath -m "${WRANGLER_PERSIST_TO}")"
python_env_real="$(realpath -m "${PYTHON_ENV}")"

for candidate in "${data_root_real}" "${wrangler_state_real}" "${python_env_real}"; do
  if [[ "${candidate}" == "${repo_real}" || "${candidate}" == "${repo_real}"/* ]]; then
    echo "OrderScope mutable/runtime paths must not be inside the source checkout: ${candidate}" >&2
    exit 2
  fi
done

mkdir -p "${DATA_ROOT}" "${WRANGLER_PERSIST_TO}" "$(dirname "${PYTHON_ENV}")"

ensure_wsl_native_path() {
  local path="$1"
  local label="$2"
  local probe="$path"

  if [[ ! -e "${probe}" ]]; then
    probe="$(dirname "${probe}")"
  fi

  local filesystem
  filesystem="$(findmnt -T "${probe}" -no FSTYPE 2>/dev/null || true)"
  case "${filesystem}" in
    9p|drvfs|ntfs|fuseblk)
      echo "${label} must be on WSL native filesystem: ${path} (${filesystem})" >&2
      exit 2
      ;;
  esac
}

ensure_wsl_native_path "${DATA_ROOT}" "OrderScope mutable data"
ensure_wsl_native_path "${WRANGLER_PERSIST_TO}" "OrderScope Wrangler state"
ensure_wsl_native_path "${PYTHON_ENV}" "OrderScope Python environment"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  active_venv_real="$(realpath -m "${VIRTUAL_ENV}")"
  if [[ "${active_venv_real}" != "${python_env_real}" ]]; then
    echo "An unexpected virtual environment is active: ${VIRTUAL_ENV}" >&2
    echo "Expected OrderScope Python environment: ${PYTHON_ENV}" >&2
    echo "Deactivate it before running this wrapper." >&2
    exit 2
  fi
fi

if [[ -d "${REPO_ROOT}/.venv" ]]; then
  echo "WARNING: legacy source-local .venv exists but will not be used: ${REPO_ROOT}/.venv" >&2
fi

export ORDERSCOPE_DATA_ROOT="${DATA_ROOT}"
export ORDERSCOPE_WRANGLER_PERSIST_TO="${WRANGLER_PERSIST_TO}"
export ORDERSCOPE_PYTHON_ENV="${PYTHON_ENV}"
export UV_PROJECT_ENVIRONMENT="${PYTHON_ENV}"
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
  bash scripts/run-local-wsl.sh sync
  bash scripts/run-local-wsl.sh api [--port PORT]
  bash scripts/run-local-wsl.sh python SCRIPT [ARGS...]
  bash scripts/run-local-wsl.sh pytest [ARGS...]
  bash scripts/run-local-wsl.sh wrangler [ARGS...]

Python commands use $UV_PROJECT_ENVIRONMENT, defaulting to
$HOME/.local/share/orderscope/venv. The wrangler command keeps local
persistence under $ORDERSCOPE_WRANGLER_PERSIST_TO. Python commands
receive $ORDERSCOPE_DATA_ROOT.
EOF
}

command_name="${1:-}"
shift || true

case "${command_name}" in
  env)
    printf 'REPO_ROOT=%s\n' "${REPO_ROOT}"
    printf 'ORDERSCOPE_DATA_ROOT=%s\n' "${ORDERSCOPE_DATA_ROOT}"
    printf 'ORDERSCOPE_WRANGLER_PERSIST_TO=%s\n' "${ORDERSCOPE_WRANGLER_PERSIST_TO}"
    printf 'ORDERSCOPE_PYTHON_ENV=%s\n' "${ORDERSCOPE_PYTHON_ENV}"
    printf 'UV_PROJECT_ENVIRONMENT=%s\n' "${UV_PROJECT_ENVIRONMENT}"
    ;;
  sync)
    exec uv sync --locked "$@"
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
