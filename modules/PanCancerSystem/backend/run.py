"""Development server runner for PanCancerSystem."""

from __future__ import annotations

import uvicorn

from backend.config import settings


def main() -> None:
    """Run the PanCancerSystem via uvicorn."""
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
