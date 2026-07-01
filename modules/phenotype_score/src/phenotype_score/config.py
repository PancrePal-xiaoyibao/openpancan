"""OpenPanCan Phenotype Score configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Environment-configurable settings for the Phenotype Score service."""

    UPLOAD_DIR: str = os.getenv("PS_UPLOAD_DIR", str(PROJECT_ROOT / "temp_uploads" / "phenotype_score"))
    OUTPUT_DIR: str = os.getenv("PS_OUTPUT_DIR", str(PROJECT_ROOT / "outputs" / "phenotype_score"))
    MAX_WORKERS: int = int(os.getenv("PS_MAX_WORKERS", "4"))


settings = Settings()
