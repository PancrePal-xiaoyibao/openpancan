"""Pydantic schemas for the OpenPanCan Variant Rank module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatusEnum(str, Enum):
    """Possible states for a ranking job."""
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class JobSubmitResponse(BaseModel):
    """Response returned after submitting a ranking job."""
    job_id: str = Field(..., description="Unique identifier for the ranking job")
    status: JobStatusEnum = Field(default=JobStatusEnum.queued, description="Initial job status")
    filename: str = Field(..., description="Original uploaded filename")


class JobStatus(BaseModel):
    """Full status record for a ranking job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Current job state")
    input: Optional[str] = Field(default=None, description="Path to uploaded input file")
    filename: str = Field(..., description="Original uploaded filename")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(default=None, description="When processing began")
    elapsed: Optional[float] = Field(default=None, description="Seconds from start to finish")
    output: Optional[str] = Field(default=None, description="Path to ranked output CSV")
    error: Optional[str] = Field(default=None, description="Error message if job failed")


class HealthResponse(BaseModel):
    """Health-check response."""
    status: str = Field(default="ok", description="Service health status")


class JobListResponse(BaseModel):
    """Summary listing of all jobs."""
    jobs: list[JobStatus] = Field(default_factory=list, description="All ranking jobs")


# ---------------------------------------------------------------------------
# Upload form fields  (used in the API endpoint signature)
# ---------------------------------------------------------------------------
# FastAPI interprets these as multipart form fields when used with UploadFile.
# We declare them here for reference; the actual endpoint uses FastAPI's
# Form / File dependencies directly, so this model is not used as a Pydantic
# body validator but serves as documentation of expected form fields.
#
#   file            : UploadFile   (required – VEP / variant CSV)
#   gene_score_file : UploadFile   (optional – gene-level score CSV)
#   ppi_score_file  : UploadFile   (optional – PPI score CSV)
# ---------------------------------------------------------------------------
