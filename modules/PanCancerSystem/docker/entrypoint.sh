#!/bin/bash
# =============================================================================
# OpenPanCan - Docker entrypoint script
# =============================================================================
#
# Initializes the database and starts supervisord to manage nginx + uvicorn.
#
# =============================================================================

set -e

echo "============================================"
echo " OpenPanCan - Starting..."
echo "============================================"

# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------
echo "[entrypoint] Initializing database..."

# Ensure data directory exists
mkdir -p /data

# Run database migrations / table creation
cd /app
python -c "
import sys
sys.path.insert(0, '/app')

try:
    from backend.database import init_db
    init_db()
    print('[entrypoint] Database initialized successfully.')
except Exception as e:
    print(f'[entrypoint] Warning: Could not initialize database: {e}')
    print('[entrypoint] Continuing anyway - database may be created on first request.')
"

# ---------------------------------------------------------------------------
# Verify nginx config
# ---------------------------------------------------------------------------
echo "[entrypoint] Verifying nginx configuration..."
nginx -t 2>&1 || {
    echo "[entrypoint] WARNING: nginx config check failed, but continuing..."
}

# ---------------------------------------------------------------------------
# Start supervisord
# ---------------------------------------------------------------------------
echo "[entrypoint] Starting services via supervisord..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/openpancan.conf
