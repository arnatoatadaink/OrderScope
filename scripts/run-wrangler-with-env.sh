#!/usr/bin/env bash

set -euo pipefail

if [[ "$#" -eq 0 ]]; then
  echo "usage: $0 <wrangler arguments...>" >&2
  exit 2
fi

explicit_env=""
for ((index = 1; index <= $#; index += 1)); do
  argument="${!index}"
  case "${argument}" in
    --env)
      next_index=$((index + 1))
      explicit_env="${!next_index:-}"
      if [[ -z "${explicit_env}" || "${explicit_env}" == -* ]]; then
        echo "ERROR: --env requires a non-empty environment name" >&2
        exit 2
      fi
      ;;
    --env=*)
      explicit_env="${argument#--env=}"
      if [[ -z "${explicit_env}" ]]; then
        echo "ERROR: --env requires a non-empty environment name" >&2
        exit 2
      fi
      ;;
  esac
done

configured_env="${CLOUDFLARE_ENV:-}"
if [[ -n "${configured_env}" && ! "${configured_env}" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]]; then
  echo "ERROR: CLOUDFLARE_ENV contains an invalid environment name" >&2
  exit 2
fi

if [[ -n "${explicit_env}" && -n "${configured_env}" && "${explicit_env}" != "${configured_env}" ]]; then
  echo "ERROR: --env (${explicit_env}) conflicts with CLOUDFLARE_ENV (${configured_env})" >&2
  exit 2
fi

if [[ -z "${explicit_env}" ]]; then
  if [[ -z "${configured_env}" ]]; then
    echo "ERROR: Cloudflare environment is required; pass --env <name> or set CLOUDFLARE_ENV" >&2
    exit 2
  fi
  set -- "$@" --env "${configured_env}"
fi

exec npx wrangler "$@"
