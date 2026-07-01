"""Cancer Patient CRUD endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import CancerPatient
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    age: int | None = None
    sex: str | None = None
    ethnicity: str | None = None
    diagnosis: str | None = None
    tumor_location: str | None = None
    tumor_stage: str | None = None
    tumor_grade: str | None = None
    histology_type: str | None = None
    ca19_9_level: float | None = None
    biomarkers: dict[str, Any] | None = None
    treatment_history: list[dict[str, Any]] | None = None
    hpo_terms: list[dict[str, Any]] | None = None
    family_history: str | None = None
    smoking_status: str | None = None
    alcohol_history: str | None = None


class PatientUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    sex: str | None = None
    ethnicity: str | None = None
    diagnosis: str | None = None
    tumor_location: str | None = None
    tumor_stage: str | None = None
    tumor_grade: str | None = None
    histology_type: str | None = None
    ca19_9_level: float | None = None
    biomarkers: dict[str, Any] | None = None
    treatment_history: list[dict[str, Any]] | None = None
    hpo_terms: list[dict[str, Any]] | None = None
    family_history: str | None = None
    smoking_status: str | None = None
    alcohol_history: str | None = None


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int | None = None
    sex: str | None = None
    ethnicity: str | None = None
    diagnosis: str | None = None
    tumor_location: str | None = None
    tumor_stage: str | None = None
    tumor_grade: str | None = None
    histology_type: str | None = None
    ca19_9_level: float | None = None
    biomarkers: dict[str, Any] | None = None
    treatment_history: list[dict[str, Any]] | None = None
    hpo_terms: list[dict[str, Any]] | None = None
    family_history: str | None = None
    smoking_status: str | None = None
    alcohol_history: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    total: int
    patients: list[PatientResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=PatientListResponse, tags=["patients"])
async def list_patients(
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=50, ge=1, le=200, description="Max records to return"),
    search: str | None = Query(default=None, description="Search by name"),
    tumor_stage: str | None = Query(default=None, description="Filter by tumor stage"),
    gene: str | None = Query(default=None, description="Filter by mutated gene"),
    db: AsyncSession = Depends(get_db),
) -> PatientListResponse:
    """List cancer patients with optional filtering."""
    query = select(CancerPatient)

    if search:
        query = query.where(CancerPatient.name.ilike(f"%{search}%"))
    if tumor_stage:
        query = query.where(CancerPatient.tumor_stage == tumor_stage)
    if gene:
        # Filter patients with a specific gene mutation in biomarkers JSON
        query = query.where(CancerPatient.biomarkers.op("json_extract")(f"$.{gene}") == "mutated")

    # Count total
    count_query = select(CancerPatient)
    if search:
        count_query = count_query.where(CancerPatient.name.ilike(f"%{search}%"))
    if tumor_stage:
        count_query = count_query.where(CancerPatient.tumor_stage == tumor_stage)

    result = await db.execute(count_query)
    total = len(result.scalars().all())

    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(CancerPatient.updated_at.desc())
    result = await db.execute(query)
    patients = result.scalars().all()

    return PatientListResponse(
        total=total,
        patients=[PatientResponse.model_validate(p) for p in patients],
    )


@router.post("/", response_model=PatientResponse, status_code=201, tags=["patients"])
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Create a new pancreatic cancer patient record."""
    patient = CancerPatient(**data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return PatientResponse.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientResponse, tags=["patients"])
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Get a specific patient by ID."""
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")
    return PatientResponse.model_validate(patient)


@router.put("/{patient_id}", response_model=PatientResponse, tags=["patients"])
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    """Update an existing patient record."""
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(patient, key, value)

    patient.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(patient)
    return PatientResponse.model_validate(patient)


@router.delete("/{patient_id}", status_code=204, tags=["patients"])
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a patient and all associated records."""
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {patient_id}")

    await db.delete(patient)
    await db.commit()
