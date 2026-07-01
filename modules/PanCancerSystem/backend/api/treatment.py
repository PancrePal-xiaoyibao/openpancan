"""Treatment record CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CancerPatient, SomaticVariant, TreatmentRecord
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TreatmentCreate(BaseModel):
    patient_id: int
    treatment_type: str = Field(..., description="surgery / chemotherapy / radiation / targeted_therapy / immunotherapy")
    drug_name: str | None = None
    regimen: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    response: str | None = None  # CR / PR / SD / PD
    notes: str | None = None


class TreatmentUpdate(BaseModel):
    treatment_type: str | None = None
    drug_name: str | None = None
    regimen: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    response: str | None = None
    notes: str | None = None


class TreatmentResponse(BaseModel):
    id: int
    patient_id: int
    treatment_type: str
    drug_name: str | None = None
    regimen: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    response: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class TreatmentListResponse(BaseModel):
    total: int
    treatments: list[TreatmentResponse]


class TreatmentRecommendation(BaseModel):
    patient_id: int
    variant_genes: list[str]
    recommendations: list[dict[str, str]]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/patient/{patient_id}", response_model=TreatmentListResponse, tags=["treatment"])
async def list_treatments(
    patient_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> TreatmentListResponse:
    """List treatment records for a patient."""
    query = select(TreatmentRecord).where(TreatmentRecord.patient_id == patient_id)

    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    query = query.order_by(TreatmentRecord.start_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    treatments = result.scalars().all()

    return TreatmentListResponse(
        total=total,
        treatments=[TreatmentResponse.model_validate(t) for t in treatments],
    )


@router.post("/", response_model=TreatmentResponse, status_code=201, tags=["treatment"])
async def create_treatment(
    data: TreatmentCreate,
    db: AsyncSession = Depends(get_db),
) -> TreatmentResponse:
    """Create a treatment record."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    valid_types = {"surgery", "chemotherapy", "radiation", "targeted_therapy", "immunotherapy"}
    if data.treatment_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid treatment_type. Must be one of: {', '.join(valid_types)}",
        )

    treatment = TreatmentRecord(**data.model_dump())
    db.add(treatment)
    await db.commit()
    await db.refresh(treatment)
    return TreatmentResponse.model_validate(treatment)


@router.get("/{treatment_id}", response_model=TreatmentResponse, tags=["treatment"])
async def get_treatment(
    treatment_id: int,
    db: AsyncSession = Depends(get_db),
) -> TreatmentResponse:
    """Get a specific treatment record."""
    result = await db.execute(
        select(TreatmentRecord).where(TreatmentRecord.id == treatment_id)
    )
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail=f"Treatment not found: {treatment_id}")
    return TreatmentResponse.model_validate(treatment)


@router.put("/{treatment_id}", response_model=TreatmentResponse, tags=["treatment"])
async def update_treatment(
    treatment_id: int,
    data: TreatmentUpdate,
    db: AsyncSession = Depends(get_db),
) -> TreatmentResponse:
    """Update a treatment record."""
    result = await db.execute(
        select(TreatmentRecord).where(TreatmentRecord.id == treatment_id)
    )
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail=f"Treatment not found: {treatment_id}")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(treatment, key, value)

    await db.commit()
    await db.refresh(treatment)
    return TreatmentResponse.model_validate(treatment)


@router.delete("/{treatment_id}", status_code=204, tags=["treatment"])
async def delete_treatment(
    treatment_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a treatment record."""
    result = await db.execute(
        select(TreatmentRecord).where(TreatmentRecord.id == treatment_id)
    )
    treatment = result.scalar_one_or_none()
    if not treatment:
        raise HTTPException(status_code=404, detail=f"Treatment not found: {treatment_id}")

    await db.delete(treatment)
    await db.commit()


@router.get("/patient/{patient_id}/recommendations", response_model=TreatmentRecommendation, tags=["treatment"])
async def get_treatment_recommendations(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
) -> TreatmentRecommendation:
    """Get treatment recommendations based on patient's variant profile."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    # Get patient's somatic variant genes
    var_result = await db.execute(
        select(SomaticVariant).where(SomaticVariant.patient_id == patient_id)
    )
    somatic_variants = var_result.scalars().all()
    variant_genes = list({v.gene for v in somatic_variants if v.gene})

    # Generate recommendations based on gene mutations
    recommendations: list[dict[str, str]] = []

    gene_treatment_map: dict[str, list[dict[str, str]]] = {
        "KRAS": [
            {"treatment": "Sotorasib", "type": "targeted_therapy", "rationale": "KRAS G12C inhibitor (if G12C mutation present)"},
            {"treatment": "Adagrasib", "type": "targeted_therapy", "rationale": "KRAS G12C inhibitor"},
        ],
        "BRCA1": [
            {"treatment": "Olaparib", "type": "targeted_therapy", "rationale": "PARP inhibitor for BRCA1-mutated pancreatic cancer"},
            {"treatment": "Rucaparib", "type": "targeted_therapy", "rationale": "PARP inhibitor"},
        ],
        "BRCA2": [
            {"treatment": "Olaparib", "type": "targeted_therapy", "rationale": "PARP inhibitor for BRCA2-mutated pancreatic cancer"},
            {"treatment": "Niraparib", "type": "targeted_therapy", "rationale": "PARP inhibitor maintenance"},
        ],
        "TP53": [
            {"treatment": "APR-246", "type": "targeted_therapy", "rationale": "TP53 reactivator (clinical trial)"},
        ],
        "CDKN2A": [
            {"treatment": "Palbociclib", "type": "targeted_therapy", "rationale": "CDK4/6 inhibitor for CDKN2A loss"},
        ],
        "SMAD4": [
            {"treatment": "Galunisertib", "type": "targeted_therapy", "rationale": "TGF-beta receptor inhibitor (clinical trial)"},
        ],
        "PIK3CA": [
            {"treatment": "Alpelisib", "type": "targeted_therapy", "rationale": "PI3K alpha inhibitor"},
        ],
        "HER2": [
            {"treatment": "Trastuzumab", "type": "targeted_therapy", "rationale": "Anti-HER2 therapy"},
        ],
        "NTRK1": [
            {"treatment": "Larotrectinib", "type": "targeted_therapy", "rationale": "TRK inhibitor for NTRK fusions"},
        ],
        "NTRK2": [
            {"treatment": "Entrectinib", "type": "targeted_therapy", "rationale": "TRK inhibitor for NTRK fusions"},
        ],
        "NTRK3": [
            {"treatment": "Larotrectinib", "type": "targeted_therapy", "rationale": "TRK inhibitor for NTRK fusions"},
        ],
        "MSI-H": [
            {"treatment": "Pembrolizumab", "type": "immunotherapy", "rationale": "Anti-PD1 for MSI-H tumors"},
        ],
    }

    for gene in variant_genes:
        if gene in gene_treatment_map:
            for rec in gene_treatment_map[gene]:
                if rec not in recommendations:
                    recommendations.append(rec)

    # Add standard-of-care options
    recommendations.extend([
        {"treatment": "FOLFIRINOX", "type": "chemotherapy", "rationale": "First-line combination chemotherapy"},
        {"treatment": "Gemcitabine + nab-Paclitaxel", "type": "chemotherapy", "rationale": "Standard first-line regimen"},
        {"treatment": "Gemcitabine monotherapy", "type": "chemotherapy", "rationale": "Option for patients with poor performance status"},
    ])

    return TreatmentRecommendation(
        patient_id=patient_id,
        variant_genes=variant_genes,
        recommendations=recommendations,
    )
