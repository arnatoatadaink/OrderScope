#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_BASE="${ORDERSCOPE_DATA_BASE:-${HOME}/data/orderscope}"

if [[ "${DATA_BASE}" != /* ]]; then
  echo "ORDERSCOPE_DATA_BASE must be an absolute WSL path" >&2
  exit 2
fi

repo_real="$(realpath "${REPO_ROOT}")"
data_base_real="$(realpath -m "${DATA_BASE}")"
if [[ "${data_base_real}" == "${repo_real}" || "${data_base_real}" == "${repo_real}"/* ]]; then
  echo "migration target must be outside the source checkout" >&2
  exit 2
fi

source_var="${REPO_ROOT}/var"
source_wrangler="${REPO_ROOT}/.wrangler/state"
target_local="${DATA_BASE}/local"
target_wrangler="${DATA_BASE}/wrangler-state"
manifest="${DATA_BASE}/migration-manifest-$(date -u +%Y%m%dT%H%M%SZ).txt"

for source in "${source_var}" "${source_wrangler}"; do
  if [[ ! -d "${source}" ]]; then
    echo "missing migration source: ${source}" >&2
    exit 1
  fi
done

mkdir -p "${target_local}" "${target_wrangler}"

for target in "${target_local}" "${target_wrangler}"; do
  if [[ -n "$(find "${target}" -mindepth 1 -print -quit)" ]]; then
    echo "migration target is not empty; refusing to overwrite live data: ${target}" >&2
    exit 2
  fi
done

for path in "${target_local}" "${target_wrangler}"; do
  filesystem="$(findmnt -T "${path}" -no FSTYPE 2>/dev/null || true)"
  case "${filesystem}" in
    9p|drvfs|ntfs|fuseblk)
      echo "migration target must be on WSL native filesystem: ${path} (${filesystem})" >&2
      exit 2
      ;;
  esac
done

rsync -a "${source_var}/" "${target_local}/"
rsync -a "${source_wrangler}/" "${target_wrangler}/"

{
  printf '# OrderScope local data migration manifest\n'
  printf 'created_at_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf 'source_checkout=%s\n' "${REPO_ROOT}"
  printf 'source_var=%s\n' "${source_var}"
  printf 'source_wrangler_state=%s\n' "${source_wrangler}"
  printf 'target_local=%s\n' "${target_local}"
  printf 'target_wrangler_state=%s\n' "${target_wrangler}"
  printf '\n[local]\n'
  (cd "${target_local}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
  printf '\n[wrangler-state]\n'
  (cd "${target_wrangler}" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "${manifest}"

printf 'migration_manifest=%s\n' "${manifest}"
printf 'local_files=%s\n' "$(find "${target_local}" -type f | wc -l)"
printf 'wrangler_state_files=%s\n' "$(find "${target_wrangler}" -type f | wc -l)"
printf 'local_sha256=%s\n' "$( (cd "${target_local}" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum) | awk '{print $1}' )"
printf 'wrangler_state_sha256=%s\n' "$( (cd "${target_wrangler}" && find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum) | awk '{print $1}' )"
