"""System settings endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.config import settings

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SystemSettingsResponse(BaseModel):
    """Read-only view of current system settings."""

    database_url: str
    module_urls: dict[str, str]
    llm_model_name: str
    cors_origins: list[str]
    port: int
    version: str = "0.1.0"


class SettingsUpdateRequest(BaseModel):
    llm_api_key: str | None = None
    llm_api_base_url: str | None = None
    llm_model_name: str | None = None
    cors_origins: list[str] | None = None
    oncokb_api_key: str | None = None


class SettingsUpdateResponse(BaseModel):
    message: str
    updated_fields: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=SystemSettingsResponse, tags=["settings"])
async def get_settings() -> SystemSettingsResponse:
    """Get current system settings."""
    return SystemSettingsResponse(
        database_url=_mask_password(settings.DATABASE_URL),
        module_urls={
            "vep_api": settings.VEP_API_BASE_URL,
            "phenotype_rag_api": settings.PHENOTYPE_RAG_API_BASE_URL,
            "phenotype_score_api": settings.PHENOTYPE_SCORE_API_BASE_URL,
            "ppi_score_api": settings.PPI_SCORE_API_BASE_URL,
            "variant_rank_api": settings.VARIANT_RANK_API_BASE_URL,
            "report_api": settings.REPORT_API_BASE_URL,
        },
        llm_model_name=settings.LLM_MODEL_NAME,
        cors_origins=settings.CORS_ORIGINS,
        port=settings.PORT,
    )


@router.put("/", response_model=SettingsUpdateResponse, tags=["settings"])
async def update_settings(data: SettingsUpdateRequest) -> SettingsUpdateResponse:
    """Update system settings at runtime.

    Note: Some settings may require a restart to take full effect.
    """
    updated: list[str] = []

    if data.llm_api_key is not None:
        settings.LLM_API_KEY = data.llm_api_key
        updated.append("llm_api_key")

    if data.llm_api_base_url is not None:
        settings.LLM_API_BASE_URL = data.llm_api_base_url
        updated.append("llm_api_base_url")

    if data.llm_model_name is not None:
        settings.LLM_MODEL_NAME = data.llm_model_name
        updated.append("llm_model_name")

    if data.cors_origins is not None:
        settings.CORS_ORIGINS = data.cors_origins
        updated.append("cors_origins")

    if data.oncokb_api_key is not None:
        settings.ONCOKB_API_KEY = data.oncokb_api_key
        updated.append("oncokb_api_key")

    return SettingsUpdateResponse(
        message=f"Settings updated: {', '.join(updated)}",
        updated_fields=updated,
    )


def _mask_password(url: str) -> str:
    """Mask password in database URL for security."""
    if "@" in url and "://" in url:
        prefix, rest = url.split("://", 1)
        if "@" in rest:
            auth_host = rest.split("@", 1)
            if ":" in auth_host[0]:
                user = auth_host[0].split(":")[0]
                return f"{prefix}://{user}:****@{auth_host[1]}"
    return url
