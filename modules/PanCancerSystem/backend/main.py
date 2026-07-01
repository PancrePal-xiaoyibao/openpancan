"""OpenPanCan PanCancerSystem – FastAPI main application.

Pancreatic cancer patient management and clinical analysis web application.
Mounts REST API routes and a WebSocket endpoint for patient chat.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pan_cancer_system")

# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------
from backend.api import (  # noqa: E402
    acmg,
    amp_asco_cap,
    chat,
    germline_variants,
    health,
    patients,
    report,
    settings as settings_router,
    somatic_variants,
    treatment,
    trials,
    variants,
)

# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    # Startup
    logger.info("PanCancerSystem starting up...")

    # Ensure directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.REPORT_DIR).mkdir(parents=True, exist_ok=True)

    # Initialize database
    try:
        from backend.database.session import init_db

        await init_db()
        logger.info("Database initialized successfully")
    except Exception as exc:
        logger.warning("Database initialization skipped: %s", exc)

    yield

    # Shutdown
    logger.info("PanCancerSystem shutting down...")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan PanCancerSystem",
    description=(
        "Pancreatic cancer patient management and clinical analysis system. "
        "Manages patient records, somatic and germline variants, ACMG/AMP "
        "classification, treatment tracking, clinical report generation, "
        "clinical trial matching, and AI-powered clinical chat."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount API routers
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api/health")
app.include_router(patients.router, prefix="/api/patients")
app.include_router(variants.router, prefix="/api/variants")
app.include_router(somatic_variants.router, prefix="/api/somatic")
app.include_router(germline_variants.router, prefix="/api/germline")
app.include_router(acmg.router, prefix="/api/acmg")
app.include_router(amp_asco_cap.router, prefix="/api/amp-asco-cap")
app.include_router(treatment.router, prefix="/api/treatment")
app.include_router(report.router, prefix="/api/report")
app.include_router(trials.router, prefix="/api/trials")
app.include_router(chat.router, prefix="/api/chat")
app.include_router(settings_router.router, prefix="/api/settings")

# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root welcome endpoint."""
    return {
        "service": "OpenPanCan PanCancerSystem",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health",
    }
