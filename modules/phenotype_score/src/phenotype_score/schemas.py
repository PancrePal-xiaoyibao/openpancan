"""Pydantic schemas for the Phenotype Score module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatusEnum(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class RunSubmitResponse(BaseModel):
    uid: str = Field(..., description="Unique run identifier")
    status: str = Field(default="queued")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunStatus(BaseModel):
    uid: str
    status: str
    input: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_files: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


class FileEntry(BaseModel):
    name: str
    url: str
