"""
OpenPanCan Phenotype Score – FastAPI server.

Scores genes and variants by their relevance to pancreatic cancer
phenotypes using COSMIC, TCGA, and OncoKB data.
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

from phenotype_score.cancer_scoring import CancerPhenotypeScorer
from phenotype_score.config import settings
from phenotype_score.schemas import (
    FileEntry,
    HealthResponse,
    RunStatus,
    RunSubmitResponse,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phenotype_score.api")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan Phenotype Score",
    description=(
        "Phenotype-based gene and variant scoring for pancreatic cancer "
        "genomic analysis. Scores genes by relevance to pancreatic cancer "
        "phenotypes using TCGA PAAD frequencies and curated gene-phenotype "
        "associations."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------
_runs: dict[str, dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def _generate_uid() -> str:
    raw = f"{time.time_ns()}-{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _process_run(uid: str, vep_path: str, hpo_path: str | None) -> None:
    """Background job: score gene and variant phenotypes."""
    try:
        _runs[uid]["status"] = "running"
        _runs[uid]["started_at"] = datetime.now(timezone.utc)

        # Read VEP output
        vep_df = pd.read_csv(vep_path)

        # Read HPO file (optional)
        hpo_ids: list[str] = []
        if hpo_path:
            try:
                with open(hpo_path) as f:
                    hpo_ids = [line.strip() for line in f if line.strip()]
            except Exception:
                pass

        # Run scorer
        scorer = CancerPhenotypeScorer()
        result = scorer.run(vep_df)

        # Write outputs
        gene_path = os.path.join(settings.OUTPUT_DIR, f"{uid}_gene_phenotype_score.csv")
        variant_path = os.path.join(settings.OUTPUT_DIR, f"{uid}_variant_phenotype_score.csv")

        result["gene_scores"].to_csv(gene_path, index=False)
        result["variant_scores"].to_csv(variant_path, index=False)

        _runs[uid]["status"] = "completed"
        _runs[uid]["completed_at"] = datetime.now(timezone.utc)
        _runs[uid]["output_files"] = [
            "gene_phenotype_score.csv",
            "variant_phenotype_score.csv",
        ]
        logger.info("Run %s completed: %d genes, %d variants scored",
                    uid, len(result["gene_scores"]), len(result["variant_scores"]))

    except Exception as exc:
        logger.exception("Run %s failed", uid)
        _runs[uid]["status"] = "failed"
        _runs[uid]["error"] = str(exc)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/runs", response_model=RunSubmitResponse)
async def create_run(
    file: UploadFile = File(...),
    hpo_file: UploadFile | None = File(default=None),
    hgvs: str = Form(default="true"),
) -> RunSubmitResponse:
    """
    Upload a VEP-annotated CSV for phenotype scoring.

    Optional hpo_file can provide HPO IDs to filter scoring.
    """
    filename = file.filename or "variants.csv"
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be .csv")

    uid = _generate_uid()
    run_dir = os.path.join(settings.UPLOAD_DIR, uid)
    os.makedirs(run_dir, exist_ok=True)

    # Save main file
    vep_path = os.path.join(run_dir, filename)
    with open(vep_path, "wb") as f:
        f.write(await file.read())

    # Save optional HPO file
    hpo_path: str | None = None
    if hpo_file and hpo_file.filename:
        hpo_path = os.path.join(run_dir, hpo_file.filename)
        with open(hpo_path, "wb") as f:
            f.write(await hpo_file.read())

    # Register run
    now = datetime.now(timezone.utc)
    _runs[uid] = {
        "uid": uid,
        "status": "queued",
        "input": vep_path,
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "output_files": [],
        "error": None,
    }

    _executor.submit(_process_run, uid, vep_path, hpo_path)

    logger.info("Run %s queued for %s", uid, filename)
    return RunSubmitResponse(uid=uid, status="queued", created_at=now)


@app.get("/runs/{uid}", response_model=RunStatus)
async def get_run_status(uid: str) -> RunStatus:
    """Get the status of a phenotype scoring run."""
    run = _runs.get(uid)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {uid}")
    return RunStatus(**run)


@app.get("/runs/{uid}/files", response_model=list[FileEntry])
async def list_run_files(uid: str) -> list[FileEntry]:
    """List output files for a completed run."""
    run = _runs.get(uid)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {uid}")
    if run["status"] != "completed":
        raise HTTPException(status_code=409, detail=f"Run not completed (status: {run['status']})")

    files = []
    for fname in run.get("output_files", []):
        files.append(FileEntry(name=fname, url=f"/runs/{uid}/files/{fname}"))
    return files


@app.get("/runs/{uid}/files/{filename}")
async def download_run_file(uid: str, filename: str):
    """Download a specific output file from a phenotype scoring run."""
    run = _runs.get(uid)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {uid}")
    if filename not in run.get("output_files", []):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    file_path = os.path.join(settings.OUTPUT_DIR, f"{uid}_{filename}")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Output file not available on disk")

    return FileResponse(path=file_path, filename=filename, media_type="text/csv")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the Phenotype Score service via uvicorn."""
    uvicorn.run(
        "phenotype_score.api:app",
        host="0.0.0.0",
        port=8003,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
