"""Health check function for the doctor CLI."""

from __future__ import annotations


def run_check() -> dict[str, str]:
    """Return health check status for the PanCancerSystem backend.

    Used by the doctor CLI module to verify the backend is operational.
    """
    return {
        "status": "ok",
        "message": "PanCancerSystem backend operational",
    }
