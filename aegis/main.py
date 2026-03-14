"""Aegis FastAPI application.

Endpoints:
  POST  /v1/audits                        — Submit an audit job
  GET   /v1/audits/{audit_id}             — Poll audit status / get report
  GET   /v1/audits/{audit_id}/findings    — Get findings only (convenience)
  GET   /health                           — Health check
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from aegis.agent import run_audit
from aegis.models import (
    AuditRequest,
    AuditStatus,
    FindingsResponse,
    HealthResponse,
    PollResponse,
    SubmitResponse,
)
from aegis.queue import audit_queue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configure and start the audit queue on startup, stop on shutdown."""
    audit_queue.set_runner(run_audit)
    await audit_queue.start()
    logger.info("Aegis API ready")
    yield
    await audit_queue.stop()
    logger.info("Aegis API shutdown complete")


app = FastAPI(
    title="Aegis UI Governance API",
    description=(
        "Audits AI-generated UI code against design system policy packs. "
        "Returns structured findings with severity, dimension, and fix suggestions."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/v1/audits", response_model=SubmitResponse, status_code=202)
async def submit_audit(request: AuditRequest):
    """Submit an audit job.

    Returns immediately with an audit_id and poll_url.
    The audit runs asynchronously in the background.
    """
    # Basic validation
    mode = request.inferred_mode()
    if mode.value == "validation" and not request.code:
        raise HTTPException(
            status_code=422,
            detail="Validation mode requires 'code' field with file contents.",
        )
    if mode.value == "comparison" and not request.repo_url:
        raise HTTPException(
            status_code=422,
            detail="Comparison mode requires 'repo_url' field.",
        )

    audit_id = await audit_queue.submit(request)
    return SubmitResponse(
        audit_id=audit_id,
        status=AuditStatus.pending,
        poll_url=f"/v1/audits/{audit_id}",
    )


@app.get("/v1/audits/{audit_id}", response_model=PollResponse)
async def poll_audit(audit_id: str):
    """Poll an audit job for its current status.

    Returns the full report when status = 'complete'.
    """
    job = audit_queue.get_job(audit_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Audit '{audit_id}' not found.")

    return PollResponse(
        audit_id=job.audit_id,
        status=job.status,
        report=job.report if job.status == AuditStatus.complete else None,
        error=job.error if job.status == AuditStatus.failed else None,
    )


@app.get("/v1/audits/{audit_id}/findings", response_model=FindingsResponse)
async def get_findings(audit_id: str):
    """Convenience endpoint — return findings only, without the full report envelope."""
    job = audit_queue.get_job(audit_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Audit '{audit_id}' not found.")

    if job.status != AuditStatus.complete:
        return FindingsResponse(
            audit_id=audit_id,
            status=None,
            findings=[],
            summary=None,
        )

    report = job.report
    return FindingsResponse(
        audit_id=audit_id,
        status=report.status,
        findings=report.findings,
        summary=report.summary,
    )
