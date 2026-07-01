"""OpenPanCan PPI Score configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Environment-configurable settings for the PPI Score service."""

    UPLOAD_DIR: str = os.getenv("PPI_UPLOAD_DIR", str(PROJECT_ROOT / "temp_uploads" / "ppi_score"))
    OUTPUT_DIR: str = os.getenv("PPI_OUTPUT_DIR", str(PROJECT_ROOT / "outputs" / "ppi_score"))
    PPI_DB_PATH: str = os.getenv("PPI_DB_PATH", str(PROJECT_ROOT / "reference_data" / "ppi"))
    MAX_WORKERS: int = int(os.getenv("PPI_MAX_WORKERS", "4"))


settings = Settings()
