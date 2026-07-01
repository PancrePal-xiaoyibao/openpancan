"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["health"])
async def health_check() -> dict[str, str]:
    """Return system health status."""
    return {"status": "ok", "service": "PanCancerSystem", "version": "0.1.0"}
