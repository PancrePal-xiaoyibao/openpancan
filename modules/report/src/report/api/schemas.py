"""Pydantic schemas for the Report module."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request to generate a pancreatic cancer genomic report."""
    wide_path: str = Field(..., description="Path to ranked variant CSV")
    phenotype_path: Optional[str] = Field(default=None, description="Path to gene phenotype score CSV")
    hpo_path: Optional[str] = Field(default=None, description="Path to HPO IDs file")
    ppi_path: Optional[str] = Field(default=None, description="Path to PPI score CSV")
    symptom_text: Optional[str] = Field(default="", description="Original clinical symptom text")
    top_n: int = Field(default=5, description="Number of top variants to feature")
    cancer_type: str = Field(default="pancreatic_ductal_adenocarcinoma", description="Cancer type")


class ReportStatus(BaseModel):
    """Status of a report generation job."""
    run_id: str
    status: str
    phase: Optional[str] = None
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    error: Optional[str] = None


class SSEEvent(BaseModel):
    """Server-Sent Event payload."""
    type: str = Field(..., description="Event type: md, pdf, phase, done, error, meta")
    content: Optional[str] = Field(default=None, description="Markdown content chunk")
    pdf_url: Optional[str] = Field(default=None, description="URL to download generated PDF")
    run_id: Optional[str] = Field(default=None, description="Run identifier")
    phase: Optional[str] = Field(default=None, description="Current generation phase")
    progress: Optional[float] = Field(default=None, description="Progress 0-1")
    error: Optional[str] = Field(default=None, description="Error message")
    meta: Optional[dict] = Field(default=None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = "ok"
    version: str = "0.1.0"


class DrugRecommendation(BaseModel):
    """A cancer drug recommendation."""
    drug: str
    target: str
    biomarker: str
    evidence_level: str
    source: str
    description: str


class ClinicalTrial(BaseModel):
    """A clinical trial match."""
    nct_id: str
    title: str
    phase: str
    status: str
    biomarker_match: str
    url: str
