"""ACMG classification endpoints for germline variants."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ACMGEvidence, GermlineVariant
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ACMGClassificationUpdate(BaseModel):
    acmg_classification: str = Field(
        ...,
        description="ACMG classification: Pathogenic / Likely Pathogenic / VUS / Likely Benign / Benign",
    )


class ACMGEvidenceCreate(BaseModel):
    criterion: str = Field(..., description="e.g., PVS1, PS1, PM2, PP3, BA1, BS1, BP4")
    evidence_level: str | None = None  # Very Strong / Strong / Moderate / Supporting / Stand-alone
    description: str | None = None
    evidence_source: str | None = None
    is_applied: bool = True


class ACMGEvidenceResponse(BaseModel):
    id: int
    germline_variant_id: int
    criterion: str
    evidence_level: str | None = None
    description: str | None = None
    evidence_source: str | None = None
    is_applied: bool

    model_config = {"from_attributes": True}


class ACMGEvidenceListResponse(BaseModel):
    variant_id: int
    acmg_classification: str | None = None
    evidence_criteria: list[ACMGEvidenceResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/variant/{variant_id}", response_model=ACMGEvidenceListResponse, tags=["acmg"])
async def get_acmg_evidence(
    variant_id: int,
    db: AsyncSession = Depends(get_db),
) -> ACMGEvidenceListResponse:
    """Get ACMG criteria evidence for a germline variant."""
    result = await db.execute(
        select(GermlineVariant).where(GermlineVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Germline variant not found: {variant_id}")

    evidence_result = await db.execute(
        select(ACMGEvidence).where(ACMGEvidence.germline_variant_id == variant_id)
    )
    evidence_items = evidence_result.scalars().all()

    return ACMGEvidenceListResponse(
        variant_id=variant_id,
        acmg_classification=variant.acmg_classification,
        evidence_criteria=[ACMGEvidenceResponse.model_validate(e) for e in evidence_items],
    )


@router.put("/variant/{variant_id}/classification", response_model=ACMGEvidenceListResponse, tags=["acmg"])
async def update_acmg_classification(
    variant_id: int,
    data: ACMGClassificationUpdate,
    db: AsyncSession = Depends(get_db),
) -> ACMGEvidenceListResponse:
    """Update the ACMG classification for a germline variant."""
    result = await db.execute(
        select(GermlineVariant).where(GermlineVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Germline variant not found: {variant_id}")

    valid = {"Pathogenic", "Likely Pathogenic", "VUS", "Likely Benign", "Benign"}
    if data.acmg_classification not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid classification. Must be one of: {', '.join(valid)}",
        )

    variant.acmg_classification = data.acmg_classification
    await db.commit()
    await db.refresh(variant)

    # Return updated evidence
    evidence_result = await db.execute(
        select(ACMGEvidence).where(ACMGEvidence.germline_variant_id == variant_id)
    )
    evidence_items = evidence_result.scalars().all()

    return ACMGEvidenceListResponse(
        variant_id=variant_id,
        acmg_classification=variant.acmg_classification,
        evidence_criteria=[ACMGEvidenceResponse.model_validate(e) for e in evidence_items],
    )


@router.post("/variant/{variant_id}/evidence", response_model=ACMGEvidenceResponse, status_code=201, tags=["acmg"])
async def add_acmg_evidence(
    variant_id: int,
    data: ACMGEvidenceCreate,
    db: AsyncSession = Depends(get_db),
) -> ACMGEvidenceResponse:
    """Add an ACMG evidence criterion to a germline variant."""
    result = await db.execute(
        select(GermlineVariant).where(GermlineVariant.id == variant_id)
    )
    variant = result.scalar_one_or_none()
    if not variant:
        raise HTTPException(status_code=404, detail=f"Germline variant not found: {variant_id}")

    evidence = ACMGEvidence(
        germline_variant_id=variant_id,
        criterion=data.criterion,
        evidence_level=data.evidence_level,
        description=data.description,
        evidence_source=data.evidence_source,
        is_applied=data.is_applied,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return ACMGEvidenceResponse.model_validate(evidence)


@router.delete("/evidence/{evidence_id}", status_code=204, tags=["acmg"])
async def delete_acmg_evidence(
    evidence_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an ACMG evidence criterion."""
    result = await db.execute(
        select(ACMGEvidence).where(ACMGEvidence.id == evidence_id)
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail=f"ACMG evidence not found: {evidence_id}")

    await db.delete(evidence)
    await db.commit()
