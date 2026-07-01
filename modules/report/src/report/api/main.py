"""
OpenPanCan Report – FastAPI server with SSE streaming.

Generates comprehensive pancreatic cancer genomic analysis reports
in Markdown format, streamed via Server-Sent Events for real-time
progress updates.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from report.api.schemas import HealthResponse, ReportRequest, SSEEvent
from report.api.service import report_service

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("report.api")

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="OpenPanCan Report Generator",
    description=(
        "Pancreatic cancer genomic analysis report generation service. "
        "Produces comprehensive reports with variant interpretation, drug "
        "recommendations, and clinical trial matching via SSE streaming."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Service health check."""
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/report/stream")
async def generate_report_stream(request: ReportRequest):
    """
    Generate a pancreatic cancer genomic report via SSE streaming.

    Streams markdown content in real-time as the report is generated,
    with progress updates for each phase:
    - loading, clinical_summary, variants, variant_detail,
    - drug_recommendations, clinical_trials, gene_scores

    Final event has type "done" with the report download URL.
    """

    async def event_generator():
        async for sse_line in report_service.generate_report(request):
            # SSE line is already formatted: "data:{...}\n\n"
            # Parse it to yield as SSE event
            if sse_line.startswith("data:"):
                payload = sse_line[5:].strip()
                yield {"data": payload}
            else:
                yield {"data": sse_line}

    return EventSourceResponse(event_generator())


@app.post("/report/generate")
async def generate_report_sync(request: ReportRequest):
    """
    Generate a pancreatic cancer genomic report (non-streaming).

    Returns the complete report in a single JSON response for
    programmatic consumption.
    """
    md_sections: list[str] = []
    run_id = None
    error = None

    async for sse_line in report_service.generate_report(request):
        if sse_line.startswith("data:"):
            payload = sse_line[5:].strip()
            try:
                import json
                event = json.loads(payload)
                event_type = event.get("type", "")

                if event_type == "md":
                    md_sections.append(event.get("content", ""))
                elif event_type == "done":
                    run_id = event.get("run_id", "")
                elif event_type == "error":
                    error = event.get("error", "")
            except Exception:
                md_sections.append(payload)

    if error:
        raise HTTPException(status_code=500, detail=error)

    return {
        "run_id": run_id,
        "report_md": "\n".join(md_sections),
        "sections_count": len(md_sections),
    }


@app.get("/report/{run_id}/download/{filename}")
async def download_report(run_id: str, filename: str):
    """
    Download a generated report file.

    Supports:
    - report.md: the full Markdown report
    - report.json: the report as JSON
    """
    content = report_service.get_report(run_id)
    if not content:
        raise HTTPException(status_code=404, detail=f"Report not found: {run_id}")

    if filename == "report.md":
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=openpancan_{run_id}_report.md"},
        )
    elif filename == "report.json":
        import json
        return JSONResponse(
            content={"run_id": run_id, "report_md": content},
            headers={"Content-Disposition": f"attachment; filename=openpancan_{run_id}_report.json"},
        )

    raise HTTPException(status_code=404, detail=f"Unknown file: {filename}")


@app.get("/report/{run_id}/status")
async def report_status(run_id: str):
    """Check if a report exists for a given run ID."""
    content = report_service.get_report(run_id)
    if content:
        return {
            "run_id": run_id,
            "status": "completed",
            "size_bytes": len(content),
        }
    return {
        "run_id": run_id,
        "status": "not_found",
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Run the Report service via uvicorn."""
    uvicorn.run(
        "report.api.main:app",
        host="0.0.0.0",
        port=8006,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
