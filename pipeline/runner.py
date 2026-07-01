"""
OpenPanCan Pipeline Runner

Orchestrates the 6-step pancreatic cancer genomic analysis pipeline:

    Step 1 (optional): Phenotype RAG  – extract HPO IDs + cancer phenotypes from clinical text
    Step 2 (required):  VEP           – annotate VCF with VEP + cancer-specific fields
    Step 3 (optional):  Phenotype Score – score genes by cancer phenotype match
    Step 4 (optional):  PPI Score     – score genes by cancer pathway PPI network
    Step 5 (optional):  Variant Rank  – rank variants by cancer driver mutation evidence
    Step 6 (required):  Report        – generate pancreatic cancer genomic report (MD + PDF)

Each step communicates over local HTTP (127.0.0.1). The runner auto-detects
whether to route through the Gateway (port 8000) or directly to each module.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("openpancan.pipeline")

# ---------------------------------------------------------------------------
# Gateway vs direct routing
# ---------------------------------------------------------------------------
_GATEWAY_URL = "http://127.0.0.1:8000"
_LOCAL: dict[str, dict[str, Any]] = {
    "phenotype_rag":    {"port": 8002},
    "vep_service":      {"port": 8001},
    "phenotype_score":  {"port": 8003},
    "ppi_score":        {"port": 8004},
    "variant_rank":     {"port": 8005},
    "report":           {"port": 8006},
}

_gateway_available: bool | None = None


async def _check_gateway(client: httpx.AsyncClient) -> bool:
    """Probe the gateway to see if it is running."""
    try:
        resp = await client.get(f"{_GATEWAY_URL}/health", timeout=3.0)
        return resp.status_code == 200
    except (httpx.HTTPError, httpx.ConnectError):
        return False


async def module_request(
    client: httpx.AsyncClient,
    name: str,
    path: str,
    *,
    method: str = "GET",
    data: Any = None,
    files: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float = 300.0,
) -> httpx.Response:
    """
    Send an HTTP request to a module.

    If the Gateway is running, route through it at ``/m/{name}{path}``.
    Otherwise, send directly to the module's local port.
    """
    if _gateway_available is None:
        _gateway_available = await _check_gateway(client)
        logger.info("Gateway available: %s", _gateway_available)

    if _gateway_available:
        url = f"{_GATEWAY_URL}/m/{name}{path}"
    else:
        port = _LOCAL[name]["port"]
        url = f"http://127.0.0.1:{port}{path}"

    if files:
        return await client.request(
            method, url, files=files, data=data or {},
            params=params, timeout=timeout,
        )
    return await client.request(
        method, url, json=data, params=params, timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Job polling helper
# ---------------------------------------------------------------------------
READY_STATUSES = {"completed", "completion", "done", "succeeded"}
FAIL_STATUSES = {"failure", "failed"}


def _json_get(data: Any, dotpath: str) -> Any:
    """Navigate a JSON dict via a dot-separated path like ``status`` or ``result.status``."""
    for key in dotpath.split("."):
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


async def _poll_job(
    client: httpx.AsyncClient,
    name: str,
    poll_path: str,
    status_field: str = "status",
    *,
    interval: float = 30.0,
    max_wait: float = 21600.0,
) -> dict[str, Any]:
    """
    Poll a module's job endpoint until the status reaches a terminal state.

    Returns the full job dict on success; raises RuntimeError on failure.
    """
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        resp = await module_request(client, name, poll_path)
        job = resp.json()
        status = _json_get(job, status_field) or ""

        if status in READY_STATUSES:
            return job
        if status in FAIL_STATUSES:
            raise RuntimeError(f"Module {name} job failed: {job}")

        logger.info("Polling %s at %s – status=%s", name, poll_path, status)
        await asyncio.sleep(interval)

    raise RuntimeError(f"Module {name} job timed out after {max_wait}s")


# ---------------------------------------------------------------------------
# Step defaults for graceful degradation
# ---------------------------------------------------------------------------
def _step_defaults(step_name: str) -> dict[str, Any]:
    """Provide empty defaults for optional steps that fail or are skipped."""
    defaults = {
        "HPO_RAG": {"hpo_file": "", "hpo_ids": []},
        "Phenotype": {"gene_csv": "", "variant_csv": ""},
        "PPI": {"ppi_csv": ""},
        "Rank": {"ranked_csv": ""},
    }
    return defaults.get(step_name, {})


# ---------------------------------------------------------------------------
# Step 1: Phenotype RAG (optional)
# ---------------------------------------------------------------------------
async def step_hpo_rag(
    client: httpx.AsyncClient,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Extract HPO IDs and cancer phenotypes from clinical text."""
    symptom_text = artifacts.get("symptom_text", "")
    output_dir = Path(artifacts["output_dir"])

    if not symptom_text:
        logger.info("No symptom text provided – skipping HPO RAG step")
        return _step_defaults("HPO_RAG")

    try:
        resp = await module_request(
            client, "phenotype_rag", "/api/v1/extract",
            method="POST",
            data={
                "notes": [
                    {"patient_id": "1", "clinical_note": symptom_text}
                ],
            },
        )
        body = resp.json()
        job_id = body.get("job_id")

        if not job_id:
            logger.warning("Phenotype RAG returned no job_id – skipping")
            hpo_file = output_dir / "hpo_ids.txt"
            hpo_file.write_text("")
            return {"hpo_file": str(hpo_file), "hpo_ids": []}

        # Poll for completion
        job = await _poll_job(client, "phenotype_rag", f"/api/v1/jobs/{job_id}")
        results = job.get("results", [])

        # Extract HPO IDs
        hpo_ids = [r["hpo_id"] for r in results if r.get("hpo_id")]
        hpo_file = output_dir / "hpo_ids.txt"
        hpo_file.write_text("\n".join(hpo_ids))

        logger.info("HPO RAG extracted %d HPO terms", len(hpo_ids))
        return {"hpo_file": str(hpo_file), "hpo_ids": hpo_ids}

    except Exception as exc:
        logger.warning("Phenotype RAG step failed: %s – continuing without HPO", exc)
        hpo_file = output_dir / "hpo_ids.txt"
        hpo_file.write_text("")
        return {"hpo_file": str(hpo_file), "hpo_ids": []}


# ---------------------------------------------------------------------------
# Step 2: VEP annotation (required)
# ---------------------------------------------------------------------------
async def step_vep(
    client: httpx.AsyncClient,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Annotate VCF with VEP and cancer-specific annotation fields."""
    vcf_path = artifacts["vcf_path"]
    hpo_ids = artifacts.get("hpo_ids", [])
    output_dir = Path(artifacts["output_dir"])
    chromosomes = artifacts.get("chromosomes", "1-22")

    vcf_file = Path(vcf_path)
    if not vcf_file.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    try:
        with open(vcf_file, "rb") as f:
            resp = await module_request(
                client, "vep_service", "/run-upload",
                method="POST",
                files={"file": (vcf_file.name, f, "text/plain")},
                data={
                    "hgvs": "true",
                    "fork": "8",
                    "chromosomes": chromosomes,
                    "hpo_ids": ",".join(hpo_ids) if hpo_ids else "",
                },
            )
        body = resp.json()
        job_id = body.get("job_id")

        if not job_id:
            raise RuntimeError(f"VEP service returned no job_id: {body}")

        # Poll until VEP completes
        job = await _poll_job(
            client, "vep_service", f"/jobs/{job_id}",
            interval=180.0, max_wait=21600.0,
        )

        # Download the annotated CSV
        files_resp = await module_request(
            client, "vep_service", f"/jobs/{job_id}/files",
        )
        files_list = files_resp.json()
        # Prefer cancer-annotated output, then standard VEP output
        best_csv = None
        for fname in sorted([f["name"] for f in files_list], reverse=True):
            if fname.endswith(".cancer_annotated.csv"):
                best_csv = fname
                break
            if fname.endswith(".csv") and best_csv is None:
                best_csv = fname

        if not best_csv:
            raise RuntimeError("No CSV output found from VEP service")

        download_resp = await module_request(
            client, "vep_service",
            f"/jobs/{job_id}/files/{best_csv}",
        )
        vep_output = output_dir / "vep_output.csv"
        vep_output.write_bytes(download_resp.content)

        logger.info("VEP annotation completed: %s", vep_output)
        return {"vep_csv": str(vep_output)}

    except Exception as exc:
        logger.error("VEP step failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Step 3: Phenotype Score (optional)
# ---------------------------------------------------------------------------
async def step_phenotype(
    client: httpx.AsyncClient,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Score genes by cancer phenotype match using COSMIC and TCGA data."""
    vep_csv = artifacts.get("vep_csv", "")
    hpo_file = artifacts.get("hpo_file", "")
    output_dir = Path(artifacts["output_dir"])

    if not vep_csv:
        logger.info("No VEP CSV – skipping phenotype scoring")
        return _step_defaults("Phenotype")

    try:
        with open(vep_csv, "rb") as vep_f:
            files = {"file": ("vep_output.csv", vep_f, "text/csv")}
            data = {"hgvs": "true"}

            if hpo_file:
                with open(hpo_file, "rb") as hpo_f:
                    files["hpo_file"] = ("hpo_ids.txt", hpo_f, "text/plain")

            resp = await module_request(
                client, "phenotype_score", "/runs",
                method="POST", files=files, data=data,
            )

        body = resp.json()
        uid = body.get("uid")
        if not uid:
            logger.warning("Phenotype score returned no uid – skipping")
            return _step_defaults("Phenotype")

        # Poll for completion
        job = await _poll_job(client, "phenotype_score", f"/runs/{uid}")

        # Download gene and variant score CSVs
        gene_csv_path = output_dir / "gene_phenotype_score.csv"
        variant_csv_path = output_dir / "variant_phenotype_score.csv"

        for fname, out_path in [
            ("gene_phenotype_score.csv", gene_csv_path),
            ("variant_phenotype_score.csv", variant_csv_path),
        ]:
            try:
                dl_resp = await module_request(
                    client, "phenotype_score",
                    f"/runs/{uid}/files/{fname}",
                )
                out_path.write_bytes(dl_resp.content)
            except Exception:
                logger.warning("Failed to download %s from phenotype_score", fname)

        logger.info("Phenotype scoring completed")
        return {
            "gene_csv": str(gene_csv_path),
            "variant_csv": str(variant_csv_path),
        }

    except Exception as exc:
        logger.warning("Phenotype score step failed: %s – continuing without scores", exc)
        return _step_defaults("Phenotype")


# ---------------------------------------------------------------------------
# Step 4: PPI Score (optional)
# ---------------------------------------------------------------------------
async def step_ppi(
    client: httpx.AsyncClient,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Score genes by cancer pathway PPI network analysis."""
    gene_csv = artifacts.get("gene_csv", "")
    vep_csv = artifacts.get("vep_csv", "")
    hpo_ids = artifacts.get("hpo_ids", [])
    output_dir = Path(artifacts["output_dir"])

    if not gene_csv or not vep_csv:
        logger.info("No gene/VEP CSV – skipping PPI scoring")
        return _step_defaults("PPI")

    try:
        with open(gene_csv, "rb") as gene_f, open(vep_csv, "rb") as vep_f:
            files = {
                "phenotype_gene_csv": ("gene_phenotype_score.csv", gene_f, "text/csv"),
                "vep_output_csv": ("vep_output.csv", vep_f, "text/csv"),
            }
            data = {"hpo_ids": ",".join(hpo_ids) if hpo_ids else ""}

            resp = await module_request(
                client, "ppi_score", "/score/clean-case/upload/async",
                method="POST", files=files, data=data,
            )

        body = resp.json()
        job_id = body.get("job_id")
        if not job_id:
            logger.warning("PPI score returned no job_id – skipping")
            return _step_defaults("PPI")

        # Poll for completion
        job = await _poll_job(client, "ppi_score", f"/score/{job_id}")

        # Download PPI score CSV
        dl_resp = await module_request(
            client, "ppi_score", f"/score/{job_id}/csv",
        )
        ppi_csv_path = output_dir / "ppi_score.csv"
        ppi_csv_path.write_bytes(dl_resp.content)

        logger.info("PPI scoring completed: %s", ppi_csv_path)
        return {"ppi_csv": str(ppi_csv_path)}

    except Exception as exc:
        logger.warning("PPI score step failed: %s – continuing without PPI scores", exc)
        return _step_defaults("PPI")


# ---------------------------------------------------------------------------
# Step 5: Variant Rank (optional)
# ---------------------------------------------------------------------------
async def step_rank(
    client: httpx.AsyncClient,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Rank variants by cancer driver mutation evidence."""
    vep_csv = artifacts.get("vep_csv", "")
    gene_csv = artifacts.get("gene_csv", "")
    ppi_csv = artifacts.get("ppi_csv", "")
    output_dir = Path(artifacts["output_dir"])

    if not vep_csv:
        logger.info("No VEP CSV – skipping variant ranking")
        return _step_defaults("Rank")

    try:
        files = {"file": ("vep_output.csv", open(vep_csv, "rb"), "text/csv")}
        data = {}

        if gene_csv:
            files["gene_score_file"] = (
                "gene_phenotype_score.csv", open(gene_csv, "rb"), "text/csv",
            )
        if ppi_csv:
            files["ppi_score_file"] = (
                "ppi_score.csv", open(ppi_csv, "rb"), "text/csv",
            )

        resp = await module_request(
            client, "variant_rank", "/score/upload",
            method="POST", files=files, data=data,
        )

        # Close file handles
        for key in ["file", "gene_score_file", "ppi_score_file"]:
            fobj = files.get(key)
            if fobj and hasattr(fobj[1], "close"):
                fobj[1].close()

        body = resp.json()
        job_id = body.get("job_id")
        if not job_id:
            logger.warning("Variant rank returned no job_id – skipping")
            return _step_defaults("Rank")

        # Poll for completion
        await _poll_job(client, "variant_rank", f"/status/{job_id}")

        # Download ranked output
        dl_resp = await module_request(
            client, "variant_rank", f"/output/{job_id}",
        )
        ranked_csv_path = output_dir / "ranked_output.csv"
        ranked_csv_path.write_bytes(dl_resp.content)

        logger.info("Variant ranking completed: %s", ranked_csv_path)
        return {"ranked_csv": str(ranked_csv_path)}

    except Exception as exc:
        logger.warning("Variant rank step failed: %s – continuing without ranking", exc)
        return _step_defaults("Rank")


# ---------------------------------------------------------------------------
# Step 6: Report (required)
# ---------------------------------------------------------------------------
async def step_report(
    client: httpx.AsyncClient,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    """Generate pancreatic cancer genomic report via SSE streaming."""
    ranked_csv = artifacts.get("ranked_csv") or artifacts.get("vep_csv", "")
    gene_csv = artifacts.get("gene_csv", "")
    ppi_csv = artifacts.get("ppi_csv", "")
    hpo_file = artifacts.get("hpo_file", "")
    symptom_text = artifacts.get("symptom_text", "")
    output_dir = Path(artifacts["output_dir"])

    if not ranked_csv:
        raise RuntimeError("No ranked CSV or VEP CSV available for report generation")

    try:
        # Report module uses SSE streaming
        report_md_path = output_dir / "report.md"
        report_pdf_path = output_dir / "report.pdf"
        md_chunks: list[str] = []

        async with client.stream(
            "POST",
            f"{_GATEWAY_URL}/m/report/report/stream"
            if _gateway_available
            else f"http://127.0.0.1:8006/report/stream",
            json={
                "wide_path": ranked_csv,
                "phenotype_path": gene_csv,
                "hpo_path": hpo_file,
                "ppi_path": ppi_csv,
                "symptom_text": symptom_text,
                "top_n": 5,
                "cancer_type": "pancreatic_ductal_adenocarcinoma",
            },
            timeout=600.0,
        ) as stream:
            async for line in stream.aiter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type", "")

                if event_type == "md":
                    md_chunks.append(event.get("content", ""))
                elif event_type == "done":
                    pdf_url = event.get("pdf_url", "")
                    run_id = event.get("run_id", "")
                    # Download PDF if available
                    if pdf_url:
                        pdf_resp = await module_request(
                            client, "report", pdf_url,
                        )
                        report_pdf_path.write_bytes(pdf_resp.content)
                    break
                elif event_type == "meta":
                    logger.info("Report meta: %s", event)
                elif event_type == "error":
                    raise RuntimeError(f"Report generation error: {event}")

        # Write accumulated markdown
        report_md_path.write_text("\n".join(md_chunks))
        logger.info("Report generated: %s", report_md_path)

        return {
            "report_md": str(report_md_path),
            "report_pdf": str(report_pdf_path) if report_pdf_path.exists() else "",
        }

    except Exception as exc:
        logger.error("Report step failed: %s", exc)
        raise


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------
PIPELINE_STEPS = [
    ("HPO_RAG",     step_hpo_rag,     False),   # optional
    ("VEP",         step_vep,         True),    # required
    ("Phenotype",   step_phenotype,   False),   # optional
    ("PPI",         step_ppi,         False),   # optional
    ("Rank",        step_rank,        False),   # optional
    ("Report",      step_report,      True),    # required
]


async def run_pipeline(
    vcf_path: str,
    symptom_text: str = "",
    output_dir: str = "outputs",
    chromosomes: str = "1-22",
) -> dict[str, Any]:
    """
    Run the full 6-step pancreatic cancer genomic analysis pipeline.

    Returns an ``artifacts`` dict mapping each output file path.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    artifacts: dict[str, Any] = {
        "vcf_path": vcf_path,
        "symptom_text": symptom_text,
        "output_dir": str(output),
        "chromosomes": chromosomes,
    }

    async with httpx.AsyncClient(timeout=600.0) as client:
        # Reset gateway detection for each pipeline run
        global _gateway_available
        _gateway_available = None

        for step_name, step_fn, required in PIPELINE_STEPS:
            logger.info("=== Step: %s (required=%s) ===", step_name, required)
            try:
                result = await step_fn(client, artifacts)
                artifacts.update(result)
                logger.info("Step %s completed – artifacts: %s", step_name, list(result.keys()))
            except Exception as exc:
                if required:
                    logger.error("Required step %s FAILED – aborting pipeline", step_name)
                    raise
                logger.warning("Optional step %s failed – using defaults: %s", step_name, exc)
                artifacts.update(_step_defaults(step_name))

    logger.info("Pipeline complete. Final artifacts: %s", list(artifacts.keys()))
    return artifacts
