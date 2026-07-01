#!/bin/bash
# =============================================================================
# OpenPanCan - Docker entrypoint script (Development)
# =============================================================================

set -e

echo "============================================"
echo " OpenPanCan - Development Mode"
echo "============================================"

# Initialize database
mkdir -p /data
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
"

# Verify nginx config
nginx -t 2>&1 || echo "[entrypoint] WARNING: nginx config check failed."

# Start supervisord with dev config
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/openpancan.conf
