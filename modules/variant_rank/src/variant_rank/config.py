"""OpenPanCan Variant Rank configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Environment-configurable settings for the Variant Rank service."""

    UPLOAD_DIR: str = os.getenv("VR_UPLOAD_DIR", str(PROJECT_ROOT / "temp_uploads" / "variant_rank"))
    OUTPUT_DIR: str = os.getenv("VR_OUTPUT_DIR", str(PROJECT_ROOT / "outputs" / "variant_rank"))
    MAX_WORKERS: int = int(os.getenv("VR_MAX_WORKERS", "4"))

    # Scoring theta weights (default percentages of total score)
    THETA_WEIGHTS: dict[str, float] = {
        "clinvar_significance": 0.20,
        "consequence": 0.15,
        "vaf": 0.05,
        "cancer_hotspot": 0.15,
        "cosmic_count": 0.10,
        "oncokb_level": 0.10,
        "tcga_frequency": 0.08,
        "pathway_membership": 0.07,
        "ppi": 0.05,
        "gene_phenotype": 0.05,
    }


settings = Settings()
