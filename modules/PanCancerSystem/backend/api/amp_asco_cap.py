"""AMP/ASCO/CAP tier classification endpoints for somatic variants."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AMPASCOCAPTier, SomaticVariant
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TierCreate(BaseModel):
    tier: str = Field(..., description="Tier: I / II / III / IV")
    evidence_category: str | None = None
    clinical_significance: str | None = None
    biomarker_relevance: str | None = None
    therapeutic_relevance: str | None = None
    confidence: str | None = None  # High / Medium / Low
    notes: str | None = None


class TierResponse(BaseModel):
    id: int
    somatic_variant_id: int
    tier: str
    evidence_category: str | None = None
    clinical_significance: str | None = None
    biomarker_relevance: str | None = None
    therapeutic_relevance: str | None = None
    confidence: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class TierListResponse(BaseModel):
    variant_id: int
    tiers: list[TierResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/variant/{variant_id}", response_model=TierListResponse, tags=["amp-asco-cap"])
async def get_tiers(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> TierListResponse:
    """Get AMP/ASCO/CAP tiers for a somatic variant."""
    result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Somatic variant not found: {variant_id}")

    tier_result = await db.execute(
        select(AMPASCOCAPTier).where(AMPASCOCAPTier.somatic_variant_id == variant_id)
    )
    tiers = tier_result.scalars().all()

    return TierListResponse(
        variant_id=variant_id,
        tiers=[TierResponse.model_validate(t) for t in tiers],
    )


@router.post("/variant/{variant_id}", response_model=TierResponse, status_code=201, tags=["amp-asco-cap"])
async def assign_tier(
    variant_id: int,
    data: TierCreate,
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    """Assign an AMP/ASCO/CAP tier to a somatic variant."""
    result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Somatic variant not found: {variant_id}")

    valid_tiers = {"I", "II", "III", "IV"}
    if data.tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
        )

    tier = AMPASCOCAPTier(
        somatic_variant_id=variant_id,
        tier=data.tier,
        evidence_category=data.evidence_category,
        clinical_significance=data.clinical_significance,
        biomarker_relevance=data.biomarker_relevance,
        therapeutic_relevance=data.therapeutic_relevance,
        confidence=data.confidence,
        notes=data.notes,
    )
    db.add(tier)
    await db.commit()
    await db.refresh(tier)
    return TierResponse.model_validate(tier)


@router.put("/tier/{tier_id}", response_model=TierResponse, tags=["amp-asco-cap"])
async def update_tier(
    tier_id: int,
    data: TierCreate,
    db: AsyncSession = Depends(get_db),
) -> TierResponse:
    """Update an existing AMP/ASCO/CAP tier record."""
    result = await db.execute(
        select(AMPASCOCAPTier).where(AMPASCOCAPTier.id == tier_id)
    )
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(status_code=404, detail=f"Tier record not found: {tier_id}")

    valid_tiers = {"I", "II", "III", "IV"}
    if data.tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier. Must be one of: {', '.join(valid_tiers)}",
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tier, key, value)

    await db.commit()
    await db.refresh(tier)
    return TierResponse.model_validate(tier)


@router.delete("/tier/{tier_id}", status_code=204, tags=["amp-asco-cap"])
async def delete_tier(
    tier_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an AMP/ASCO/CAP tier record."""
    result = await db.execute(
        select(AMPASCOCAPTier).where(AMPASCOCAPTier.id == tier_id)
    )
    tier = result.scalar_one_or_none()
    if not tier:
        raise HTTPException(status_code=404, detail=f"Tier record not found: {tier_id}")

    await db.delete(tier)
    await db.commit()
