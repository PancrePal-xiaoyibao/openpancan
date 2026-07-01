"""OpenPanCan Phenotype RAG configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings:
    """Environment-configurable settings for the Phenotype RAG service."""

    LLM_ENDPOINT: str = os.getenv("PHEN_RAG_LLM_ENDPOINT", "http://localhost:11434/api/generate")
    LLM_MODEL: str = os.getenv("PHEN_RAG_LLM_MODEL", "llama3.1:8b")
    LLM_TIMEOUT: int = int(os.getenv("PHEN_RAG_LLM_TIMEOUT", "120"))
    HPO_ONTOLOGY_URL: str = os.getenv(
        "HPO_ONTOLOGY_URL",
        "https://raw.githubusercontent.com/obophenotype/human-phenotype-ontology/master/hp.json",
    )
    PROMPTS_FILE: str = os.getenv(
        "PHEN_RAG_PROMPTS",
        str(Path(__file__).parent / "cancer_prompts.json"),
    )
    MAX_WORKERS: int = int(os.getenv("PHEN_RAG_MAX_WORKERS", "4"))


settings = Settings()
