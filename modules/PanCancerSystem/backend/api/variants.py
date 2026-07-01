"""Variant query endpoints – lists variants across somatic and germline."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import GermlineVariant, SomaticVariant
from backend.database.session import get_db

router = APIRouter()


class VariantItem(BaseModel):
    id: int
    patient_id: int
    chromosome: str
    position: int
    ref: str
    alt: str
    gene: str | None = None
    variant_type: str
    source: str  # "somatic" or "germline"
    vaf: float | None = None
    consequence: str | None = None
    impact: str | None = None
    clinvar_significance: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class VariantListResponse(BaseModel):
    total: int
    variants: list[VariantItem]


@router.get("/", response_model=VariantListResponse, tags=["variants"])
async def list_variants(
    patient_id: int | None = Query(default=None, description="Filter by patient ID"),
    gene: str | None = Query(default=None, description="Filter by gene symbol"),
    variant_type: str | None = Query(default=None, description="Filter by variant type (SNV/INDEL/CNV/SV)"),
    chromosome: str | None = Query(default=None, description="Filter by chromosome"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> VariantListResponse:
    """List all variants (somatic + germline) with optional filters."""
    # Build somatic query
    som_query = select(SomaticVariant)
    if patient_id:
        som_query = som_query.where(SomaticVariant.patient_id == patient_id)
    if gene:
        som_query = som_query.where(SomaticVariant.gene == gene)
    if variant_type:
        som_query = som_query.where(SomaticVariant.variant_type == variant_type)
    if chromosome:
        som_query = som_query.where(SomaticVariant.chromosome == chromosome)

    # Build germline query
    germ_query = select(GermlineVariant)
    if patient_id:
        germ_query = germ_query.where(GermlineVariant.patient_id == patient_id)
    if gene:
        germ_query = germ_query.where(GermlineVariant.gene == gene)
    if variant_type:
        germ_query = germ_query.where(GermlineVariant.variant_type == variant_type)
    if chromosome:
        germ_query = germ_query.where(GermlineVariant.chromosome == chromosome)

    # Execute both to count
    som_result = await db.execute(som_query)
    som_all = som_result.scalars().all()

    germ_result = await db.execute(germ_query)
    germ_all = germ_result.scalars().all()

    # Convert to unified items
    items: list[VariantItem] = []
    for v in som_all:
        items.append(VariantItem(
            id=v.id,
            patient_id=v.patient_id,
            chromosome=v.chromosome,
            position=v.position,
            ref=v.ref,
            alt=v.alt,
            gene=v.gene,
            variant_type=v.variant_type,
            source="somatic",
            vaf=v.vaf,
            consequence=v.consequence,
            impact=v.impact,
            clinvar_significance=v.clinvar_significance,
            created_at=v.created_at,
        ))

    for v in germ_all:
        items.append(VariantItem(
            id=v.id,
            patient_id=v.patient_id,
            chromosome=v.chromosome,
            position=v.position,
            ref=v.ref,
            alt=v.alt,
            gene=v.gene,
            variant_type=v.variant_type,
            source="germline",
            vaf=None,
            consequence=v.consequence,
            impact=v.impact,
            clinvar_significance=v.clinvar_significance,
            created_at=v.created_at,
        ))

    total = len(items)

    # Sort by position, then apply pagination
    items.sort(key=lambda x: (x.chromosome, x.position))
    paginated = items[skip : skip + limit]

    return VariantListResponse(total=total, variants=paginated)


@router.get("/{variant_id}", response_model=VariantItem, tags=["variants"])
async def get_variant(
    variant_id: int,
    source: str = Query(..., description="Source: 'somatic' or 'germline'"),
    db: AsyncSession = Depends(get_db),
) -> VariantItem:
    """Get a single variant by ID and source."""
    if source == "somatic":
        result = await db.execute(
            select(SomaticVariant).where(SomaticVariant.id == variant_id)
        )
        v = result.scalar_one_or_none()
        if not v:
            raise HTTPException(status_code=404, detail=f"Somatic variant not found: {variant_id}")
        return VariantItem(
            id=v.id,
            patient_id=v.patient_id,
            chromosome=v.chromosome,
            position=v.position,
            ref=v.ref,
            alt=v.alt,
            gene=v.gene,
            variant_type=v.variant_type,
            source="somatic",
            vaf=v.vaf,
            consequence=v.consequence,
            impact=v.impact,
            clinvar_significance=v.clinvar_significance,
            created_at=v.created_at,
        )
    elif source == "germline":
        result = await db.execute(
            select(GermlineVariant).where(GermlineVariant.id == variant_id)
        )
        v = result.scalar_one_or_none()
        if not v:
            raise HTTPException(status_code=404, detail=f"Germline variant not found: {variant_id}")
        return VariantItem(
            id=v.id,
            patient_id=v.patient_id,
            chromosome=v.chromosome,
            position=v.position,
            ref=v.ref,
            alt=v.alt,
            gene=v.gene,
            variant_type=v.variant_type,
            source="germline",
            vaf=None,
            consequence=v.consequence,
            impact=v.impact,
            clinvar_significance=v.clinvar_significance,
            created_at=v.created_at,
        )
    else:
        raise HTTPException(status_code=400, detail="Source must be 'somatic' or 'germline'")
