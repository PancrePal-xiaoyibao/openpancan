"""OpenPanCan VEP Service configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Environment-configurable settings for the VEP service."""

    VEP_CACHE_DIR: str = os.getenv("VEP_CACHE_DIR", str(PROJECT_ROOT / "reference_data" / "vep_cache"))
    VEP_FASTA_FILE: str = os.getenv(
        "VEP_FASTA_FILE",
        str(PROJECT_ROOT / "reference_data" / "vep_cache" / "Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"),
    )
    VEP_ASSEMBLY: str = os.getenv("VEP_ASSEMBLY", "GRCh38")
    COSMIC_DATA_DIR: str = os.getenv("COSMIC_DATA_DIR", str(PROJECT_ROOT / "reference_data" / "cosmic"))
    TCGA_DATA_DIR: str = os.getenv("TCGA_DATA_DIR", str(PROJECT_ROOT / "reference_data" / "tcga"))
    UPLOAD_DIR: str = os.getenv("VEP_UPLOAD_DIR", str(PROJECT_ROOT / "temp_uploads" / "vep"))
    OUTPUT_DIR: str = os.getenv("VEP_OUTPUT_DIR", str(PROJECT_ROOT / "outputs" / "vep"))
    VEP_FORK: int = int(os.getenv("VEP_FORK", "8"))
    VEP_PLUGINS: str = os.getenv("VEP_PLUGINS", "COSMIC,OncoKB")


settings = Settings()
