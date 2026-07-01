"""OpenPanCan PanCancerSystem configuration."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _generate_secret_key() -> str:
    """Generate a random secret key for JWT signing."""
    return secrets.token_urlsafe(64)


class Settings:
    """Environment-configurable settings for the PanCancerSystem."""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./openpancan.db",
    )

    # JWT / Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", _generate_secret_key())
    ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Module service URLs
    VEP_API_BASE_URL: str = os.getenv("VEP_API_BASE_URL", "http://localhost:8001")
    PHENOTYPE_RAG_API_BASE_URL: str = os.getenv("PHENOTYPE_RAG_API_BASE_URL", "http://localhost:8002")
    PHENOTYPE_SCORE_API_BASE_URL: str = os.getenv("PHENOTYPE_SCORE_API_BASE_URL", "http://localhost:8003")
    PPI_SCORE_API_BASE_URL: str = os.getenv("PPI_SCORE_API_BASE_URL", "http://localhost:8004")
    VARIANT_RANK_API_BASE_URL: str = os.getenv("VARIANT_RANK_API_BASE_URL", "http://localhost:8005")
    REPORT_API_BASE_URL: str = os.getenv("REPORT_API_BASE_URL", "http://localhost:8006")

    # LLM configuration (for chat)
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE_URL: str = os.getenv("LLM_API_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "llama-3.1-70b-versatile")

    # External API keys
    ONCOKB_API_KEY: str = os.getenv("ONCOKB_API_KEY", "")

    # Server port
    PORT: int = int(os.getenv("PANCANCER_SYSTEM_PORT", "8007"))

    # CORS
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    # Upload / output directories
    UPLOAD_DIR: str = os.getenv("PANCANCER_UPLOAD_DIR", str(PROJECT_ROOT / "temp_uploads" / "pancancer"))
    OUTPUT_DIR: str = os.getenv("PANCANCER_OUTPUT_DIR", str(PROJECT_ROOT / "outputs" / "pancancer"))
    REPORT_DIR: str = os.getenv("PANCANCER_REPORT_DIR", str(PROJECT_ROOT / "outputs" / "reports"))


settings = Settings()
