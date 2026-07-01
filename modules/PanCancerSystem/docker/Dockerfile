# =============================================================================
# OpenPanCan - Multi-stage Docker build
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Frontend build
# ---------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install pnpm for faster, reliable installs
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy package manifests and install dependencies
COPY frontend/package.json frontend/pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# Copy frontend source and build
COPY frontend/ ./
RUN pnpm run build

# ---------------------------------------------------------------------------
# Stage 2: Backend dependencies
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install uv for fast Python package management
RUN pip install --no-cache-dir uv

# Copy the PanCancerSystem backend pyproject.toml and backend source
COPY pyproject.toml ./
COPY backend/ ./backend/

# Install Python dependencies using uv
RUN uv pip install --system --no-cache -r <(grep -E '^[[:space:]]*"[^"]+"' pyproject.toml | head -1 || echo "") \
    || uv pip install --system --no-cache fastapi uvicorn[standard] pydantic sqlalchemy aiosqlite httpx

# ---------------------------------------------------------------------------
# Stage 3: Production image
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS production

LABEL org.opencontainers.image.title="OpenPanCan"
LABEL org.opencontainers.image.description="Pancreatic Cancer Genomic Analysis System"
LABEL org.opencontainers.image.version="0.1.0"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor /var/log/opencancan

WORKDIR /app

# Copy Python and site-packages from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=backend-builder /usr/local/bin/ /usr/local/bin/

# Copy backend application code
COPY backend/ ./backend/

# Copy frontend build artifacts
COPY --from=frontend-builder /app/frontend/dist/ /usr/share/nginx/html/

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || true
COPY docker/supervisord.conf /etc/supervisor/conf.d/opencancan.conf
COPY docker/entrypoint.sh /entrypoint.sh

# Ensure nginx config directory exists
RUN mkdir -p /etc/nginx/sites-available /etc/nginx/conf.d \
    && rm -f /etc/nginx/sites-enabled/default \
    && ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default 2>/dev/null || true

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Create data directory for SQLite
RUN mkdir -p /data && chmod 777 /data

# Expose ports
# 8181 - Main web interface (nginx served frontend + API proxy)
# 8007 - Direct backend API access
EXPOSE 8181 8007

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATABASE_URL=sqlite:////data/opencancan.db

ENTRYPOINT ["/entrypoint.sh"]
