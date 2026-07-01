#!/usr/bin/env bash
# OpenPanCan – Environment loader script
# Source this file to load module-specific environment variables.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[OpenPanCan] Loading environment from ${REPO_ROOT}"

# Load root .env if it exists
if [ -f "${REPO_ROOT}/.env" ]; then
    set -a
    source "${REPO_ROOT}/.env"
    set +a
    echo "[OpenPanCan] Loaded: .env"
fi

# Load module .env files
for mod_dir in "${REPO_ROOT}"/modules/*/; do
    env_file="${mod_dir}.env"
    if [ -f "${env_file}" ]; then
        set -a
        source "${env_file}"
        set +a
        echo "[OpenPanCan] Loaded: ${env_file}"
    fi
done

echo "[OpenPanCan] Environment ready"
