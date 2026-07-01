"""Clinical report generation endpoints."""

from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.models import CancerPatient, ClinicalReport
from backend.database.session import get_db

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ReportGenerateRequest(BaseModel):
    patient_id: int
    report_type: str = Field(default="genomic", description="genomic / clinical / comprehensive")


class ReportStatusResponse(BaseModel):
    id: int
    patient_id: int
    report_type: str
    run_id: str | None = None
    summary: str | None = None
    has_markdown: bool = False
    has_pdf: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    total: int
    reports: list[ReportStatusResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_run_id() -> str:
    raw = f"{time.time_ns()}-{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _generate_report_content(
    patient: CancerPatient,
    report_type: str,
) -> str:
    """Generate a clinical report in markdown format."""
    biomarkers_str = ""
    if patient.biomarkers:
        for gene, status in patient.biomarkers.items():
            biomarkers_str += f"| {gene} | {status} |\n"

    hpo_str = ""
    if patient.hpo_terms:
        for hpo in patient.hpo_terms:
            hpo_str += f"- **{hpo.get('hpo_id', 'N/A')}**: {hpo.get('hpo_term', 'Unknown')} (confidence: {hpo.get('confidence', 'N/A')})\n"

    report = f"""# Pancreatic Cancer Clinical Report

## Patient Information

| Field | Value |
|-------|-------|
| **Name** | {patient.name} |
| **Age** | {patient.age or 'N/A'} |
| **Sex** | {patient.sex or 'N/A'} |
| **Ethnicity** | {patient.ethnicity or 'N/A'} |
| **Diagnosis** | {patient.diagnosis or 'N/A'} |
| **Tumor Location** | {patient.tumor_location or 'N/A'} |
| **Tumor Stage** | {patient.tumor_stage or 'N/A'} |
| **Tumor Grade** | {patient.tumor_grade or 'N/A'} |
| **Histology** | {patient.histology_type or 'N/A'} |
| **CA19-9 Level** | {patient.ca19_9_level or 'N/A'} U/mL |

## Biomarker Status

| Gene | Status |
|------|--------|
{biomarkers_str or '| - | No biomarker data available |'}

## Clinical Phenotypes (HPO Terms)

{hpo_str or 'No HPO terms recorded.'}

## Clinical History

- **Family History**: {patient.family_history or 'Not reported'}
- **Smoking Status**: {patient.smoking_status or 'Not reported'}
- **Alcohol History**: {patient.alcohol_history or 'Not reported'}

---

*Report Type*: {report_type}
*Generated*: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
*Run ID*: {{run_id}}
"""
    return report


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate", response_model=ReportStatusResponse, status_code=201, tags=["report"])
async def generate_report(
    data: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ReportStatusResponse:
    """Generate a clinical report for a patient."""
    # Verify patient exists
    result = await db.execute(
        select(CancerPatient).where(CancerPatient.id == data.patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient not found: {data.patient_id}")

    valid_types = {"genomic", "clinical", "comprehensive"}
    if data.report_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report_type. Must be one of: {', '.join(valid_types)}",
        )

    run_id = _generate_run_id()
    report_dir = Path(settings.REPORT_DIR)
    report_dir.mkdir(parents=True, exist_ok=True)

    # Generate report content
    content = _generate_report_content(patient, data.report_type)
    content = content.replace("{{run_id}}", run_id)

    # Save markdown file
    markdown_path = str(report_dir / f"{run_id}_report.md")
    with open(markdown_path, "w") as f:
        f.write(content)

    # Create report record
    report = ClinicalReport(
        patient_id=data.patient_id,
        report_type=data.report_type,
        run_id=run_id,
        markdown_path=markdown_path,
        pdf_path=None,
        summary=(content[:500] + "..." if len(content) > 500 else content),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportStatusResponse.model_validate(report)


@router.get("/patient/{patient_id}", response_model=ReportListResponse, tags=["report"])
async def list_reports(
    patient_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> ReportListResponse:
    """List clinical reports for a patient."""
    query = select(ClinicalReport).where(ClinicalReport.patient_id == patient_id)

    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    query = query.order_by(ClinicalReport.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    reports = result.scalars().all()

    return ReportListResponse(
        total=total,
        reports=[
            ReportStatusResponse(
                id=r.id,
                patient_id=r.patient_id,
                report_type=r.report_type,
                run_id=r.run_id,
                summary=r.summary,
                has_markdown=r.markdown_path is not None,
                has_pdf=r.pdf_path is not None,
                created_at=r.created_at,
            )
            for r in reports
        ],
    )


@router.get("/{report_id}", response_model=ReportStatusResponse, tags=["report"])
async def get_report_status(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportStatusResponse:
    """Get report status by ID."""
    result = await db.execute(
        select(ClinicalReport).where(ClinicalReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    return ReportStatusResponse(
        id=report.id,
        patient_id=report.patient_id,
        report_type=report.report_type,
        run_id=report.run_id,
        summary=report.summary,
        has_markdown=report.markdown_path is not None,
        has_pdf=report.pdf_path is not None,
        created_at=report.created_at,
    )


@router.get("/{report_id}/download", tags=["report"])
async def download_report(
    report_id: int,
    format: str = Query(default="markdown", description="markdown or pdf"),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download a generated report."""
    result = await db.execute(
        select(ClinicalReport).where(ClinicalReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    if format == "markdown" and report.markdown_path:
        file_path = report.markdown_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Markdown file not found on disk")
        return FileResponse(
            path=file_path,
            filename=f"report_{report.run_id}.md",
            media_type="text/markdown",
        )
    elif format == "pdf" and report.pdf_path:
        file_path = report.pdf_path
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found on disk")
        return FileResponse(
            path=file_path,
            filename=f"report_{report.run_id}.pdf",
            media_type="application/pdf",
        )
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Report not available in {format} format",
        )


@router.delete("/{report_id}", status_code=204, tags=["report"])
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a clinical report."""
    result = await db.execute(
        select(ClinicalReport).where(ClinicalReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    await db.delete(report)
    await db.commit()
