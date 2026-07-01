"""Pydantic schemas for the Phenotype RAG module."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class CancerPhenotypeType(str, Enum):
    """Types of cancer phenotype observations."""
    TUMOR_CHARACTERISTIC = "tumor_characteristic"
    BIOMARKER = "biomarker"
    TREATMENT = "treatment"
    SYMPTOM = "symptom"
    COMORBIDITY = "comorbidity"
    FAMILY_HISTORY = "family_history"
    METASTASIS = "metastasis"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"


class ExtractRequest(BaseModel):
    """Request body for phenotype extraction."""
    notes: list[NoteItem] = Field(
        default_factory=list,
        description="List of clinical note items to extract phenotypes from",
    )


class NoteItem(BaseModel):
    """A single clinical note item."""
    patient_id: str = Field(default="1", description="Patient identifier")
    clinical_note: str = Field(
        default="",
        description="Free-text clinical note describing patient presentation",
    )


class RunResponse(BaseModel):
    """Response after submitting an extraction job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(default="queued", description="Initial job status")


class JobStatus(BaseModel):
    """Full job status record."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(default="queued", description="Current job status")
    results: list[ResultItem] = Field(
        default_factory=list,
        description="Extracted phenotype results (populated when complete)",
    )
    error: Optional[str] = Field(default=None, description="Error message if job failed")


class ResultItem(BaseModel):
    """A single extracted phenotype result."""
    patient_id: str = Field(default="1", description="Patient identifier")
    hpo_id: Optional[str] = Field(default=None, description="HPO term ID")
    hpo_term: Optional[str] = Field(default=None, description="Human-readable HPO term name")
    phenotype_type: Optional[str] = Field(
        default=None,
        description="Category of phenotype observation",
    )
    value: Optional[str] = Field(default=None, description="Phenotype value or finding")
    confidence: float = Field(default=0.5, description="Extraction confidence score 0-1")
    evidence_span: Optional[str] = Field(
        default=None,
        description="Text span supporting this extraction",
    )
    icd10_code: Optional[str] = Field(default=None, description="Mapped ICD-10 code")
    loinc_code: Optional[str] = Field(default=None, description="Mapped LOINC code (lab results)")


class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="0.1.0", description="Service version")
