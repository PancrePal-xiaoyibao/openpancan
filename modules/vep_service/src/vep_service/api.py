"""
OpenPanCan VEP Service – FastAPI server.

Provides endpoints for uploading VCF files, running VEP annotation jobs
asynchronously, and retrieving results. Uses ThreadPoolExecutor for async
job execution.
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from vep_service.config import settings
from vep_service.schemas import (
    FileEntry,
    HealthResponse,
    JobStatusEnum,
    JobStatusResponse,
    JobSubmitResponse,
)
from vep_service.vep_runner import process_vcf_job
from vep_service.cancer_annotation import (
    PANCREATIC_CANCER_DRIVER_GENES,
    KRAS_HOTSPOT_MUTATIONS,
    add_cancer_annotations,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vep_service.api")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan VEP Service",
    description=(
        "Variant Effect Predictor (VEP) annotation service for pancreatic "
        "cancer genomic analysis. Accepts VCF uploads, runs annotation "
        "asynchronously, and provides cancer-enriched results."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------
_jobs: dict[str, dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=4)

# Ensure upload/output directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _generate_job_id() -> str:
    """Generate a unique job ID from timestamp and random hash."""
    raw = f"{time.time_ns()}-{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _run_job(job_id: str, vcf_path: str, params: dict[str, Any]) -> None:
    """Background job runner. Called from ThreadPoolExecutor."""
    try:
        _jobs[job_id]["status"] = JobStatusEnum.running
        _jobs[job_id]["started_at"] = datetime.now(timezone.utc)

        params["output_dir"] = settings.OUTPUT_DIR
        output_path = process_vcf_job(job_id, vcf_path, params)

        _jobs[job_id]["status"] = JobStatusEnum.completed
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        _jobs[job_id]["output_files"] = [os.path.basename(output_path)]
        _jobs[job_id]["output_path"] = output_path
        logger.info("Job %s completed successfully", job_id)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _jobs[job_id]["status"] = JobStatusEnum.failed
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        _jobs[job_id]["error"] = str(exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/run-upload", response_model=JobSubmitResponse)
async def run_upload(
    file: UploadFile = File(...),
    hgvs: str = Form(default="true"),
    fork: str = Form(default="8"),
    chromosomes: str = Form(default="1-22"),
    hpo_ids: str = Form(default=""),
) -> JobSubmitResponse:
    """
    Upload a VCF file and start an asynchronous VEP annotation job.

    The VCF is saved to disk, and a background thread begins processing.
    Returns immediately with a job ID for polling.
    """
    # Validate file extension
    filename = file.filename or "upload.vcf"
    if not filename.endswith((".vcf", ".vcf.gz")):
        raise HTTPException(
            status_code=400,
            detail="File must be a .vcf or .vcf.gz file",
        )

    # Save uploaded file
    job_id = _generate_job_id()
    upload_dir = os.path.join(settings.UPLOAD_DIR, job_id)
    os.makedirs(upload_dir, exist_ok=True)
    vcf_path = os.path.join(upload_dir, filename)

    try:
        with open(vcf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    # Build params
    params: dict[str, Any] = {
        "hgvs": hgvs,
        "fork": fork,
        "chromosomes": chromosomes,
        "hpo_ids": hpo_ids,
    }

    # Register job
    now = datetime.now(timezone.utc)
    _jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatusEnum.queued,
        "input_filename": filename,
        "input_path": vcf_path,
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "output_files": [],
        "error": None,
        "params": params,
    }

    # Submit to executor
    _executor.submit(_run_job, job_id, vcf_path, params)

    logger.info("Job %s queued for file: %s", job_id, filename)

    return JobSubmitResponse(
        job_id=job_id,
        status=JobStatusEnum.queued,
        created_at=now,
        status_url=f"/jobs/{job_id}",
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status of a VEP annotation job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        input_filename=job.get("input_filename"),
        created_at=job.get("created_at"),
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        output_files=job.get("output_files", []),
        error=job.get("error"),
    )


@app.get("/jobs/{job_id}/files", response_model=list[FileEntry])
async def list_job_files(job_id: str) -> list[FileEntry]:
    """List output files for a completed VEP job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job["status"] != JobStatusEnum.completed:
        raise HTTPException(
            status_code=409,
            detail=f"Job not completed yet (status: {job['status']})",
        )

    files: list[FileEntry] = []
    for fname in job.get("output_files", []):
        files.append(FileEntry(
            name=fname,
            url=f"/jobs/{job_id}/files/{fname}",
        ))

    return files


@app.get("/jobs/{job_id}/files/{filename}")
async def download_job_file(job_id: str, filename: str):
    """Download a specific output file from a VEP job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if filename not in job.get("output_files", []):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    output_path = job.get("output_path", "")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not available on disk")

    return FileResponse(
        path=output_path,
        filename=filename,
        media_type="text/csv",
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the VEP service via uvicorn."""
    uvicorn.run(
        "vep_service.api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
