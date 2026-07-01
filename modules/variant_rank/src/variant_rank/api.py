"""
OpenPanCan Variant Rank – FastAPI server.

Provides endpoints for uploading annotated variant CSV files, running
cancer driver ranking asynchronously, and retrieving ranked results.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from variant_rank.cancer_driver_rank import CancerDriverRanker
from variant_rank.config import settings
from variant_rank.dataio import merge_scores, read_variants, write_ranked
from variant_rank.schemas import (
    HealthResponse,
    JobListResponse,
    JobStatus,
    JobStatusEnum,
    JobSubmitResponse,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("variant_rank.api")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan Variant Rank",
    description=(
        "Cancer driver mutation ranking for pancreatic cancer genomic "
        "analysis. Scores and ranks variants by multi-criteria evidence "
        "including ClinVar, COSMIC, OncoKB, TCGA PAAD frequencies, "
        "pathway membership, and PPI network analysis."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# In-memory job store
# ---------------------------------------------------------------------------
_jobs: dict[str, dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _generate_job_id() -> str:
    raw = f"{time.time_ns()}-{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _run_scoring_job(job_id: str, input_path: str,
                     gene_path: str | None, ppi_path: str | None) -> None:
    """Background job: read, score, rank, and write output."""
    try:
        _jobs[job_id]["status"] = JobStatusEnum.running
        _jobs[job_id]["started_at"] = datetime.now(timezone.utc)

        # Read input variants
        vep_df = read_variants(input_path)

        # Read optional gene / PPI scores
        gene_df = None
        ppi_df = None
        if gene_path:
            try:
                import pandas as pd
                gene_df = pd.read_csv(gene_path)
            except Exception:
                logger.warning("Could not read gene score file: %s", gene_path)
        if ppi_path:
            try:
                import pandas as pd
                ppi_df = pd.read_csv(ppi_path)
            except Exception:
                logger.warning("Could not read PPI score file: %s", ppi_path)

        # Merge external scores
        vep_df = merge_scores(vep_df, gene_df, ppi_df)

        # Build score maps
        ppi_scores: dict[str, float] | None = None
        gene_scores: dict[str, float] | None = None
        if gene_df is not None and not gene_df.empty:
            if "gene" in gene_df.columns and "score" in gene_df.columns:
                gene_scores = dict(zip(gene_df["gene"], gene_df["score"]))
        if ppi_df is not None and not ppi_df.empty:
            if "gene" in ppi_df.columns and "ppi_score" in ppi_df.columns:
                ppi_scores = dict(zip(ppi_df["gene"], ppi_df["ppi_score"]))

        # Run ranker
        ranker = CancerDriverRanker()
        ranked_df = ranker.run(vep_df, ppi_scores, gene_scores)

        # Write output
        output_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_ranked.csv")
        write_ranked(ranked_df, output_path)

        elapsed = (datetime.now(timezone.utc) - _jobs[job_id]["started_at"]).total_seconds()

        _jobs[job_id]["status"] = JobStatusEnum.done
        _jobs[job_id]["elapsed"] = elapsed
        _jobs[job_id]["output"] = output_path
        logger.info("Job %s completed in %.1fs → %s", job_id, elapsed, output_path)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _jobs[job_id]["status"] = JobStatusEnum.failed
        _jobs[job_id]["elapsed"] = (
            datetime.now(timezone.utc) - _jobs[job_id]["started_at"]
        ).total_seconds()
        _jobs[job_id]["error"] = str(exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok")


@app.post("/score/upload", response_model=JobSubmitResponse)
async def score_upload(
    file: UploadFile = File(...),
    gene_score_file: UploadFile | None = File(default=None),
    ppi_score_file: UploadFile | None = File(default=None),
) -> JobSubmitResponse:
    """
    Upload a VEP-annotated variant CSV for ranking.

    Optional gene_score_file and ppi_score_file provide external
    gene-level phenotype scores and PPI network scores.
    """
    # Validate file
    filename = file.filename or "variants.csv"
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Input file must be a .csv")

    # Save main input file
    job_id = _generate_job_id()
    upload_dir = os.path.join(settings.UPLOAD_DIR, job_id)
    os.makedirs(upload_dir, exist_ok=True)

    input_path = os.path.join(upload_dir, filename)
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Save optional files
    gene_path: str | None = None
    ppi_path: str | None = None

    if gene_score_file and gene_score_file.filename:
        gene_path = os.path.join(upload_dir, gene_score_file.filename)
        with open(gene_path, "wb") as f:
            f.write(await gene_score_file.read())

    if ppi_score_file and ppi_score_file.filename:
        ppi_path = os.path.join(upload_dir, ppi_score_file.filename)
        with open(ppi_path, "wb") as f:
            f.write(await ppi_score_file.read())

    # Register job
    now = datetime.now(timezone.utc)
    _jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatusEnum.queued,
        "input": input_path,
        "filename": filename,
        "created_at": now,
        "started_at": None,
        "elapsed": None,
        "output": None,
        "error": None,
    }

    # Submit background job
    _executor.submit(_run_scoring_job, job_id, input_path, gene_path, ppi_path)

    logger.info("Job %s queued for file: %s", job_id, filename)

    return JobSubmitResponse(job_id=job_id, filename=filename)


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get the current status of a ranking job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobStatus(**job)


@app.get("/output/{job_id}")
async def get_output(job_id: str):
    """Download the ranked output CSV for a completed job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job["status"] != JobStatusEnum.done:
        raise HTTPException(
            status_code=409,
            detail=f"Job not done (status: {job['status']})",
        )

    output_path = job.get("output")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not available")

    return FileResponse(
        path=output_path,
        filename=f"{job['filename']}_ranked.csv",
        media_type="text/csv",
    )


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs() -> JobListResponse:
    """List all ranking jobs."""
    return JobListResponse(jobs=[JobStatus(**j) for j in _jobs.values()])


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the Variant Rank service via uvicorn."""
    uvicorn.run(
        "variant_rank.api:app",
        host="0.0.0.0",
        port=8005,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
