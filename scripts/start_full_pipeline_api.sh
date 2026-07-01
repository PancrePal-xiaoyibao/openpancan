#!/usr/bin/env bash
# OpenPanCan – Full pipeline API startup script
# Starts the VEP service with all cancer annotation plugins.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load environment
source "${SCRIPT_DIR}/load-env.sh"

echo "[OpenPanCan] Starting full pipeline API..."
cd "${REPO_ROOT}/modules/vep_service/src"

exec uv run --project "${REPO_ROOT}/modules/vep_service" -- \
    uvicorn vep_service.api:app \
    --host 0.0.0.0 \
    --port 8001 \
    --log-level info
