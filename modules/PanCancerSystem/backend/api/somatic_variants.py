"""Somatic variant CRUD endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CancerPatient, SomaticVariant
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SomaticVariantCreate(BaseModel):
    patient_id: int
    chromosome: str = Field(..., min_length=1)
    position: int
    ref: str = Field(..., min_length=1)
    alt: str = Field(..., min_length=1)
    gene: str | None = None
    variant_type: str = Field(default="SNV")
    vaf: float | None = None
    tumor_depth: int | None = None
    normal_depth: int | None = None
    cosmic_id: str | None = None
    oncokb_level: str | None = None
    is_cancer_hotspot: bool = False
    driver_prediction: str | None = None
    consequence: str | None = None
    impact: str | None = None
    hgvs_c: str | None = None
    hgvs_p: str | None = None
    clinvar_significance: str | None = None
    revel_score: float | None = None
    cadd_score: float | None = None
    spliceai_score: float | None = None
    gnomad_af: float | None = None
    strand_bias: float | None = None
    copy_number: float | None = None


class SomaticVariantUploadRequest(BaseModel):
    """Batch upload somatic variants for a patient."""
    patient_id: int
    variants: list[SomaticVariantCreate]


class SomaticVariantResponse(BaseModel):
    id: int
    patient_id: int
    chromosome: str
    position: int
    ref: str
    alt: str
    gene: str | None = None
    variant_type: str
    vaf: float | None = None
    tumor_depth: int | None = None
    normal_depth: int | None = None
    cosmic_id: str | None = None
    oncokb_level: str | None = None
    is_cancer_hotspot: bool = False
    driver_prediction: str | None = None
    consequence: str | None = None
    impact: str | None = None
    hgvs_c: str | None = None
    hgvs_p: str | None = None
    clinvar_significance: str | None = None
    revel_score: float | None = None
    cadd_score: float | None = None
    spliceai_score: float | None = None
    gnomad_af: float | None = None
    strand_bias: float | None = None
    copy_number: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SomaticVariantListResponse(BaseModel):
    total: int
    variants: list[SomaticVariantResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/", response_model=SomaticVariantResponse, status_code=201, tags=["somatic"])
async def create_somatic_variant(
    data: SomaticVariantCreate,
    db: AsyncSession = Depends(get_db),
) -> SomaticVariantResponse:
    """Create a single somatic variant record."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    variant = SomaticVariant(**data.model_dump())
    db.add(variant)
    await db.commit()
    await db.refresh(variant)
    return SomaticVariantResponse.model_validate(variant)


@router.post("/upload", response_model=SomaticVariantListResponse, status_code=201, tags=["somatic"])
async def upload_somatic_variants(
    data: SomaticVariantUploadRequest,
    db: AsyncSession = Depends(get_db),
) -> SomaticVariantListResponse:
    """Batch upload somatic variants for a patient."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    created: list[SomaticVariant] = []
    for var_data in data.variants:
        var_data.patient_id = data.patient_id
        variant = SomaticVariant(**var_data.model_dump())
        db.add(variant)
        created.append(variant)

    await db.commit()
    for v in created:
        await db.refresh(v)

    return SomaticVariantListResponse(
        total=len(created),
        variants=[SomaticVariantResponse.model_validate(v) for v in created],
    )


@router.get("/patient/{patient_id}", response_model=SomaticVariantListResponse, tags=["somatic"])
async def list_somatic_variants_by_patient(
    patient_id: int,
    vaf_min: float | None = Query(default=None, description="Minimum VAF filter"),
    vaf_max: float | None = Query(default=None, description="Maximum VAF filter"),
    gene: str | None = Query(default=None, description="Filter by gene"),
    variant_type: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> SomaticVariantListResponse:
    """List somatic variants for a specific patient with optional VAF and gene filters."""
    query = select(SomaticVariant).where(SomaticVariant.patient_id == patient_id)

    if vaf_min is not None:
        query = query.where(SomaticVariant.vaf >= vaf_min)
    if vaf_max is not None:
        query = query.where(SomaticVariant.vaf <= vaf_max)
    if gene:
        query = query.where(SomaticVariant.gene == gene)
    if variant_type:
        query = query.where(SomaticVariant.variant_type == variant_type)

    # Count
    count_result = await db.execute(query)
    all_variants = count_result.scalars().all()
    total = len(all_variants)

    # Paginate
    query = query.order_by(SomaticVariant.chromosome, SomaticVariant.position)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    variants = result.scalars().all()

    return SomaticVariantListResponse(
        total=total,
        variants=[SomaticVariantResponse.model_validate(v) for v in variants],
    )


@router.get("/{variant_id}", response_model=SomaticVariantResponse, tags=["somatic"])
async def get_somatic_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> SomaticVariantResponse:
    """Get a specific somatic variant by ID."""
    result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Somatic variant not found: {variant_id}")
    return SomaticVariantResponse.model_validate(variant)


@router.delete("/{variant_id}", status_code=204, tags=["somatic"])
async def delete_somatic_variant(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a somatic variant."""
    result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Somatic variant not found: {variant_id}")

    await db.delete(variant)
    await db.commit()
