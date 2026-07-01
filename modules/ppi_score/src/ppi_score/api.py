"""
OpenPanCan PPI Score – FastAPI server.

Scores genes based on cancer pathway protein-protein interaction (PPI)
network analysis for pancreatic cancer.
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

import pandas as pd
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ppi_score.cancer_ppi import CancerPPIScorer
from ppi_score.config import settings
from ppi_score.schemas import HealthResponse, ScoreStatus, ScoreSubmitResponse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ppi_score.api")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan PPI Score",
    description=(
        "Protein-Protein Interaction (PPI) scoring for pancreatic cancer "
        "genomic analysis. Scores genes by their interaction network "
        "relevance to pancreatic cancer driver pathways."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------
_jobs: dict[str, dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def _generate_job_id() -> str:
    raw = f"{time.time_ns()}-{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _process_ppi_job(
    job_id: str,
    vep_path: str,
    gene_path: str | None,
    hpo_ids: list[str],
) -> None:
    """Background job: run PPI scoring."""
    try:
        _jobs[job_id]["status"] = "running"

        vep_df = pd.read_csv(vep_path)
        gene_df = pd.read_csv(gene_path) if gene_path else None

        scorer = CancerPPIScorer()
        result = scorer.run(vep_df, gene_df, hpo_ids if hpo_ids else None)

        # Write PPI network scores
        ppi_network_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_ppi_network.csv")
        result["ppi_network"].to_csv(ppi_network_path, index=False)

        # Write variant-level PPI scores
        ppi_scores_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}_ppi_scores.csv")
        result["ppi_scores"].to_csv(ppi_scores_path, index=False)

        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        _jobs[job_id]["output_csv"] = ppi_network_path
        logger.info("Job %s completed", job_id)

    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/score/clean-case/upload/async", response_model=ScoreSubmitResponse)
async def score_upload_async(
    phenotype_gene_csv: UploadFile = File(...),
    vep_output_csv: UploadFile = File(...),
    hpo_ids: str = Form(default=""),
) -> ScoreSubmitResponse:
    """
    Upload phenotype gene scores and VEP output for PPI scoring.

    Accepts two CSV files and optional HPO IDs.
    """
    job_id = _generate_job_id()
    upload_dir = os.path.join(settings.UPLOAD_DIR, job_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Save uploaded files
    vep_path = os.path.join(upload_dir, vep_output_csv.filename or "vep_output.csv")
    with open(vep_path, "wb") as f:
        f.write(await vep_output_csv.read())

    gene_path = os.path.join(upload_dir, phenotype_gene_csv.filename or "gene_scores.csv")
    with open(gene_path, "wb") as f:
        f.write(await phenotype_gene_csv.read())

    hpo_list = [h.strip() for h in hpo_ids.split(",") if h.strip()]

    # Register job
    now = datetime.now(timezone.utc)
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "input_type": "ppi_clean_case",
        "created_at": now,
        "completed_at": None,
        "output_csv": None,
        "error": None,
    }

    _executor.submit(_process_ppi_job, job_id, vep_path, gene_path, hpo_list)

    logger.info("Job %s queued (input_type=ppi_clean_case)", job_id)
    return ScoreSubmitResponse(job_id=job_id)


@app.get("/score/{job_id}", response_model=ScoreStatus)
async def get_score_status(job_id: str) -> ScoreStatus:
    """Get the status of a PPI scoring job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return ScoreStatus(**job)


@app.get("/score/{job_id}/csv")
async def get_score_csv(job_id: str):
    """Download the PPI network score CSV for a completed job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Job not done (status: {job['status']})",
        )

    output_path = job.get("output_csv")
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output CSV not available")

    return FileResponse(
        path=output_path,
        filename=f"{job_id}_ppi_network.csv",
        media_type="text/csv",
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the PPI Score service via uvicorn."""
    uvicorn.run(
        "ppi_score.api:app",
        host="0.0.0.0",
        port=8004,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
