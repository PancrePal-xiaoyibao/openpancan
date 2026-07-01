"""Pydantic schemas for the PPI Score module."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatusEnum(str, Enum):
    queued = "queued"
    running = "running"
    done = "done"
    failed = "failed"


class ScoreSubmitResponse(BaseModel):
    job_id: str
    status: str = "queued"


class ScoreStatus(BaseModel):
    job_id: str
    status: str
    input_type: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_csv: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
