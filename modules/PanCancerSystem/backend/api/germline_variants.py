"""Germline variant CRUD endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CancerPatient, GermlineVariant
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class GermlineVariantCreate(BaseModel):
    patient_id: int
    chromosome: str = Field(..., min_length=1)
    position: int
    ref: str = Field(..., min_length=1)
    alt: str = Field(..., min_length=1)
    gene: str | None = None
    variant_type: str = Field(default="SNV")
    consequence: str | None = None
    impact: str | None = None
    hgvs_c: str | None = None
    hgvs_p: str | None = None
    clinvar_significance: str | None = None
    gnomad_af: float | None = None
    revel_score: float | None = None
    cadd_score: float | None = None
    spliceai_score: float | None = None
    acmg_classification: str | None = None


class GermlineVariantUploadRequest(BaseModel):
    """Batch upload germline variants for a patient."""
    patient_id: int
    variants: list[GermlineVariantCreate]


class GermlineVariantResponse(BaseModel):
    id: int
    patient_id: int
    chromosome: str
    position: int
    ref: str
    alt: str
    gene: str | None = None
    variant_type: str
    consequence: str | None = None
    impact: str | None = None
    hgvs_c: str | None = None
    hgvs_p: str | None = None
    clinvar_significance: str | None = None
    gnomad_af: float | None = None
    revel_score: float | None = None
    cadd_score: float | None = None
    spliceai_score: float | None = None
    acmg_classification: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GermlineVariantListResponse(BaseModel):
    total: int
    variants: list[GermlineVariantResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=GermlineVariantResponse, status_code=201, tags=["germline"])
async def create_germline_variant(
    data: GermlineVariantCreate,
    db: AsyncSession = Depends(get_db),
) -> GermlineVariantResponse:
    """Create a single germline variant record."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    variant = GermlineVariant(**data.model_dump())
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return GermlineVariantResponse.model_validate(variant)


@router.post("/upload", response_model=GermlineVariantListResponse, status_code=201, tags=["germline"])
async def upload_germline_variants(
    data: GermlineVariantUploadRequest,
    db: AsyncSession = Depends(get_db),
) -> GermlineVariantListResponse:
    """Batch upload germline variants for a patient."""
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    created: list[GermlineVariant] = []
    for var_data in data.variants:
        var_data.patient_id = data.patient_id
        variant = GermlineVariant(**var_data.model_dump())
        db.add(variant)
        created.append(variant)

    await db.commit()
    for v in created:
        await db.refresh(v)

    return GermlineVariantListResponse(
        total=len(created),
        variants=[GermlineVariantResponse.model_validate(v) for v in created],
    )


@router.get("/patient/{patient_id}", response_model=GermlineVariantListResponse, tags=["germline"])
async def list_germline_variants_by_patient(
    patient_id: int,
    acmg_classification: str | None = Query(default=None, description="Filter by ACMG classification"),
    gene: str | None = Query(default=None, description="Filter by gene"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> GermlineVariantListResponse:
    """List germline variants for a specific patient with optional ACMG filter."""
    query = select(GermlineVariant).where(GermlineVariant.patient_id == patient_id)

    if acmg_classification:
        query = query.where(GermlineVariant.acmg_classification == acmg_classification)
    if gene:
        query = query.where(GermlineVariant.gene == gene)

    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    query = query.order_by(GermlineVariant.chromosome, GermlineVariant.position)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    variants = result.scalars().all()

    return GermlineVariantListResponse(
        total=total,
        variants=[GermlineVariantResponse.model_validate(v) for v in variants],
    )


@router.get("/{variant_id}", response_model=GermlineVariantResponse, tags=["germline"])
async def get_germline_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> GermlineVariantResponse:
    """Get a specific germline variant by ID."""
    result = await db.execute(
        select(GermlineVariant).where(GermlineVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Germline variant not found: {variant_id}")
    return GermlineVariantResponse.model_validate(variant)


@router.delete("/{variant_id}", status_code=204, tags=["germline"])
async def delete_germline_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a germline variant."""
    result = await db.execute(
        select(GermlineVariant).where(GermlineVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Germline variant not found: {variant_id}")

    await db.delete(variant)
    await db.commit()
