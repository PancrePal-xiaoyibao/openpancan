"""
OpenPanCan Phenotype RAG – FastAPI server.

Provides endpoints for extracting cancer phenotypes (HPO terms, tumor
characteristics, biomarker status, treatment history) from clinical text.
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
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from phenotype_rag.pipeline import CancerPhenotypePipeline
from phenotype_rag.schemas import (
    ExtractRequest,
    HealthResponse,
    JobStatus,
    ResultItem,
    RunResponse,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("phenotype_rag.server")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan Phenotype RAG",
    description=(
        "Cancer phenotype extraction service for pancreatic cancer genomic "
        "analysis. Extracts HPO terms, tumor characteristics, biomarker "
        "status, and treatment history from clinical text using rule-based "
        "and LLM-assisted NLP."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------
_jobs: dict[str, dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=4)

# Pipeline instance (shared)
_pipeline = CancerPhenotypePipeline(use_llm=False)


def _generate_job_id() -> str:
    raw = f"{time.time_ns()}-{os.urandom(4).hex()}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/api/v1/extract", response_model=RunResponse)
async def extract_phenotypes(request: ExtractRequest) -> RunResponse:
    """
    Extract cancer phenotypes from clinical notes.

    Accepts one or more clinical notes and returns a job ID for polling
    the extraction results.
    """
    if not request.notes:
        raise HTTPException(status_code=400, detail="At least one clinical note is required")

    job_id = _generate_job_id()

    def _process() -> None:
        try:
            _jobs[job_id]["status"] = "running"
            results: list[ResultItem] = []

            for note_item in request.notes:
                pipeline_result = _pipeline.run(note_item.clinical_note)

                # Convert HPO terms to ResultItems
                for hpo in pipeline_result["hpo_terms"]:
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        hpo_id=hpo.get("hpo_id"),
                        hpo_term=hpo.get("hpo_term"),
                        phenotype_type=hpo.get("phenotype_type"),
                        value=f"{hpo.get('hpo_term')}",
                        confidence=hpo.get("confidence", 0.5),
                        evidence_span=hpo.get("evidence_span"),
                    ))

                # Tumor characteristics as ResultItems
                tumor = pipeline_result["tumor_characteristics"]
                if tumor.get("tumor_location"):
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="tumor_characteristic",
                        value=f"Location: {tumor['tumor_location']}",
                        confidence=tumor.get("confidence", 0.6),
                    ))
                if tumor.get("tumor_size_cm"):
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="tumor_characteristic",
                        value=f"Size: {tumor['tumor_size_cm']} cm",
                        confidence=tumor.get("confidence", 0.6),
                    ))
                if tumor.get("tnm_stage"):
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="tumor_characteristic",
                        value=f"Stage: {tumor['tnm_stage']}",
                        confidence=tumor.get("confidence", 0.6),
                    ))
                if tumor.get("histology"):
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="tumor_characteristic",
                        value=f"Histology: {tumor['histology']}",
                        confidence=tumor.get("confidence", 0.6),
                    ))
                if tumor.get("grade"):
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="tumor_characteristic",
                        value=f"Grade: {tumor['grade']}",
                        confidence=tumor.get("confidence", 0.6),
                    ))

                # Biomarkers
                for bm in pipeline_result["biomarkers"]:
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="biomarker",
                        value=f"{bm['biomarker']}: {bm['result']} ({bm.get('method', '')})",
                        confidence=bm.get("confidence", 0.5),
                    ))

                # Treatments
                for tx in pipeline_result["treatments"]:
                    results.append(ResultItem(
                        patient_id=note_item.patient_id,
                        phenotype_type="treatment",
                        value=f"{tx['type'].upper()}: {tx['treatment']} ({tx.get('date_or_status', '')})",
                        confidence=tx.get("confidence", 0.5),
                    ))

            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["results"] = results
            logger.info("Job %s completed with %d results", job_id, len(results))

        except Exception as exc:
            logger.exception("Job %s failed", job_id)
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["error"] = str(exc)

    # Initialize job record
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "results": [],
        "error": None,
    }

    # Submit to thread pool
    _executor.submit(_process)

    logger.info("Job %s queued for phenotype extraction", job_id)
    return RunResponse(job_id=job_id, status="queued")


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str) -> JobStatus:
    """Get the status and results of a phenotype extraction job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return JobStatus(**job)


@app.get("/api/v1/jobs/{job_id}/result")
async def get_job_result(job_id: str):
    """Get the full extraction results for a completed job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'Unknown error')}",
        )

    results = job.get("results", [])
    return {
        "job_id": job_id,
        "status": job["status"],
        "count": len(results),
        "results": [r.model_dump() for r in results] if results else [],
    }


@app.get("/api/v1/jobs/{job_id}/download/{filename}")
async def download_hpo_file(job_id: str, filename: str):
    """
    Download extracted HPO IDs as a text file (one per line).

    The filename should be 'hpo_ids.txt' to get HPO IDs.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job["status"] not in ("completed",):
        raise HTTPException(
            status_code=409,
            detail=f"Job not completed (status: {job['status']})",
        )

    results = job.get("results", [])

    if filename == "hpo_ids.txt":
        hpo_ids = [
            r.hpo_id for r in results
            if isinstance(r, ResultItem) and r.hpo_id
        ] if results else [
            r.get("hpo_id") for r in [r.model_dump() if hasattr(r, 'model_dump') else r for r in results]
            if r and r.get("hpo_id")
        ]

        content = "\n".join(sorted(set(hpo_ids)))
        return JSONResponse({"content": content, "hpo_ids": sorted(set(hpo_ids))})

    raise HTTPException(status_code=404, detail=f"Unknown file: {filename}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the Phenotype RAG service via uvicorn."""
    uvicorn.run(
        "phenotype_rag.server:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
