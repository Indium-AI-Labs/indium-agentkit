#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
INSTALLER="${SCRIPT_DIR}/install.py"

if ! command -v python3 >/dev/null 2>&1; then
  printf 'error: Python 3 is required to run the installer\n' >&2
  exit 1
fi

if [[ $# -gt 0 && "$1" != -* ]]; then
  PROJECT_DIR="$1"
  TARGET_IDE="${2:-all}"
  exec python3 "${INSTALLER}" \
    --scope project \
    --project-dir "${PROJECT_DIR}" \
    --target "${TARGET_IDE}" \
    --item all \
    --mode link \
    --include-context
fi

exec python3 "${INSTALLER}" "$@"
