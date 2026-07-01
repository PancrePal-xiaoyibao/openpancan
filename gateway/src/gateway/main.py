"""
OpenPanCan Gateway Orchestrator

Spawns and manages 7 pancreatic cancer analysis modules as subprocesses,
provides transparent HTTP dispatch to each module, and exposes a unified
entry point on port 8000.

Architecture:
    Gateway (8000) ──> vep_service       (8001)
                    ──> phenotype_rag    (8002)
                    ──> phenotype_score  (8003)
                    ──> ppi_score        (8004)
                    ──> variant_rank     (8005)
                    ──> report           (8006)
                    ──> PanCancerSystem  (8007)
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("openpancan.gateway")

# ---------------------------------------------------------------------------
# Repository root (two levels up from this file)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------------------
# Module registry – each entry describes how to launch and health-check a
# pancreatic cancer analysis microservice.
# ---------------------------------------------------------------------------
MODULES: dict[str, dict[str, Any]] = {
    "vep_service": {
        "port": 8001,
        "project_dir": "modules/vep_service",
        "health": "/health",
        "cmd": ["uvicorn", "vep_service.api:app", "--host", "0.0.0.0", "--port", "8001"],
        "cwd": "modules/vep_service/src",
        "env": {},
    },
    "phenotype_rag": {
        "port": 8002,
        "project_dir": "modules/phenotype_rag",
        "health": "/api/v1/health",
        "cmd": ["uvicorn", "phenotype_rag.server:app", "--host", "0.0.0.0", "--port", "8002"],
        "cwd": "modules/phenotype_rag/src",
        "env": {},
    },
    "phenotype_score": {
        "port": 8003,
        "project_dir": "modules/phenotype_score",
        "health": "/health",
        "cmd": ["uvicorn", "phenotype_score.api:app", "--host", "0.0.0.0", "--port", "8003"],
        "cwd": "modules/phenotype_score/src",
        "env": {},
    },
    "ppi_score": {
        "port": 8004,
        "project_dir": "modules/ppi_score",
        "health": "/health",
        "cmd": ["uvicorn", "ppi_score.api:app", "--host", "0.0.0.0", "--port", "8004"],
        "cwd": "modules/ppi_score/src",
        "env": {},
    },
    "variant_rank": {
        "port": 8005,
        "project_dir": "modules/variant_rank",
        "health": "/health",
        "cmd": ["uvicorn", "variant_rank.api:app", "--host", "0.0.0.0", "--port", "8005"],
        "cwd": "modules/variant_rank/src",
        "env": {},
    },
    "report": {
        "port": 8006,
        "project_dir": "modules/report",
        "health": "/health",
        "cmd": ["uvicorn", "report.api.main:app", "--host", "0.0.0.0", "--port", "8006"],
        "cwd": "modules/report/src",
        "env": {},
    },
    "PanCancerSystem": {
        "port": 8007,
        "project_dir": "modules/PanCancerSystem",
        "health": "/api/health",
        "cmd": ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"],
        "cwd": "modules/PanCancerSystem/backend",
        "env": {},
    },
}

# ---------------------------------------------------------------------------
# Subprocess management
# ---------------------------------------------------------------------------
_procs: dict[str, subprocess.Popen] = {}
_dead: set[str] = set()


def start_module(name: str, cfg: dict[str, Any]) -> None:
    """Launch a single module as a subprocess via ``uv run``."""
    project_dir = REPO_ROOT / cfg["project_dir"]
    cwd = REPO_ROOT / cfg.get("cwd", cfg["project_dir"])

    # Build the command: uv run --project <dir> -- <cmd...>
    cmd = ["uv", "run", "--project", str(project_dir), "--"] + cfg["cmd"]

    env = {**os.environ, **cfg.get("env", {})}
    logger.info("Starting %s: %s (cwd=%s)", name, " ".join(cmd), cwd)

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stderr=subprocess.DEVNULL,
        )
        # Quick check – if the process exits within 3 s it likely failed
        try:
            ret = proc.wait(timeout=3)
            if ret != 0:
                logger.error("Module %s exited immediately with code %d", name, ret)
                _dead.add(name)
                return
        except subprocess.TimeoutExpired:
            pass  # still running, which is the happy path

        _procs[name] = proc
        logger.info("Module %s started (pid=%d)", name, proc.pid)
    except FileNotFoundError:
        logger.error("uv not found in PATH – cannot start module %s", name)
        _dead.add(name)
    except Exception:
        logger.exception("Failed to start module %s", name)
        _dead.add(name)


def start_modules() -> None:
    """Start all registered modules."""
    for name, cfg in MODULES.items():
        start_module(name, cfg)


def stop_modules() -> None:
    """Terminate all running module processes."""
    for name, proc in _procs.items():
        if proc.poll() is None:
            logger.info("Stopping %s (pid=%d)", name, proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    _procs.clear()
    _dead.clear()


# ---------------------------------------------------------------------------
# Health-check polling
# ---------------------------------------------------------------------------
async def wait_healthy(
    client: httpx.AsyncClient,
    timeout: float = 60.0,
    interval: float = 2.0,
) -> list[str]:
    """Poll each module's health endpoint until all respond or *timeout* elapses."""
    ready: list[str] = []
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        for name, cfg in MODULES.items():
            if name in ready or name in _dead:
                continue
            port = cfg["port"]
            health_path = cfg["health"]
            url = f"http://127.0.0.1:{port}{health_path}"
            try:
                resp = await client.get(url, timeout=3.0)
                if resp.status_code == 200:
                    logger.info("Module %s is healthy", name)
                    ready.append(name)
            except (httpx.HTTPError, httpx.ConnectError):
                pass  # not ready yet
        if len(ready) + len(_dead) >= len(MODULES):
            break
        await asyncio.sleep(interval)

    not_ready = [n for n in MODULES if n not in ready and n not in _dead]
    if not_ready:
        logger.warning("Modules not ready after %.0fs: %s", timeout, not_ready)

    return ready


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start modules, wait for health, then serve; tear down on shutdown."""
    start_modules()
    async with httpx.AsyncClient(timeout=120.0) as client:
        ready = await wait_healthy(client)
        app.state.ready_modules = ready
        app.state.http_client = client
        logger.info(
            "Gateway ready – %d/%d modules online: %s",
            len(ready),
            len(MODULES),
            ready,
        )
        yield
    stop_modules()


app = FastAPI(
    title="OpenPanCan Gateway",
    description=(
        "Orchestrator for the OpenPanCan pancreatic cancer genomic analysis "
        "system. Proxies requests to 7 independent microservice modules."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Health & status endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "modules_online": getattr(app.state, "ready_modules", []),
        "modules_dead": list(_dead),
    }


@app.get("/pipeline/status")
async def pipeline_status():
    """Return a summary of every module's port and readiness."""
    ready = getattr(app.state, "ready_modules", [])
    return {
        name: {
            "port": cfg["port"],
            "healthy": name in ready,
            "dead": name in _dead,
        }
        for name, cfg in MODULES.items()
    }


# ---------------------------------------------------------------------------
# Transparent dispatch
# ---------------------------------------------------------------------------
@app.api_route(
    "/m/{module}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
)
async def dispatch(module: str, path: str, request: Request):
    """
    Proxy a request to the given module.

    The gateway forwards the raw request body and returns the upstream
    response verbatim, preserving content-type and status code.
    """
    if module not in MODULES:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Unknown module: {module}"},
        )
    ready = getattr(app.state, "ready_modules", [])
    if module not in ready:
        return JSONResponse(
            status_code=503,
            content={"detail": f"Module {module} is not available"},
        )

    cfg = MODULES[module]
    port = cfg["port"]
    upstream = f"http://127.0.0.1:{port}/{path}"
    client: httpx.AsyncClient = app.state.http_client

    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    resp = await client.request(
        method=request.method,
        url=upstream,
        content=body,
        headers=headers,
        params=request.query_params,
    )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "gateway.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
