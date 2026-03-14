"""Async in-memory job queue for Aegis audits.

Design goals:
- Non-blocking: audit jobs run as background tasks, API returns immediately
- Redis-ready: the interface is designed so an asyncio.Queue can be swapped
  for a Redis-backed queue (Celery, ARQ) without changing the API contract
- Bounded concurrency: AEGIS_MAX_CONCURRENT_AUDITS limits parallel Claude calls
- Thread-safe: uses asyncio primitives only (no threading)
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Awaitable

from ulid import ULID

from aegis.config import settings
from aegis.models import AuditJob, AuditRequest, AuditStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Job store (in-memory dict, swap for Redis in production)
# ---------------------------------------------------------------------------

_jobs: dict[str, AuditJob] = {}


def get_job(audit_id: str) -> AuditJob | None:
    return _jobs.get(audit_id)


def list_jobs() -> list[AuditJob]:
    return list(_jobs.values())


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


class AuditQueue:
    """
    Manages the lifecycle of audit jobs.

    Usage:
        queue = AuditQueue()
        await queue.start()                    # call on app startup
        audit_id = await queue.submit(request) # returns immediately
        job = queue.get_job(audit_id)          # poll for status
        await queue.stop()                     # call on app shutdown
    """

    def __init__(self, runner: Callable[[AuditJob], Awaitable] | None = None):
        # Defer asyncio primitives to start() so they're bound to the correct
        # event loop. Creating them at __init__ time (module import) causes
        # "bound to a different event loop" errors when tests use fresh loops.
        self._queue: asyncio.Queue[AuditJob] | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._runner = runner  # injected to avoid circular imports
        self._worker_task: asyncio.Task | None = None
        self._running = False

    def set_runner(self, runner: Callable[[AuditJob], Awaitable]):
        """Set the audit runner function (to avoid circular imports at module load)."""
        self._runner = runner

    async def start(self):
        """Start the background worker loop. Call on FastAPI startup."""
        # Create asyncio primitives in the running event loop
        self._queue = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(settings.aegis_max_concurrent_audits)
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("AuditQueue started")

    async def stop(self):
        """Gracefully stop the queue. Call on FastAPI shutdown."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("AuditQueue stopped")

    async def submit(self, request: AuditRequest) -> str:
        """
        Create a new audit job and enqueue it.
        Returns the audit_id immediately (non-blocking).
        """
        audit_id = f"aud_{ULID()}"
        job = AuditJob(
            audit_id=audit_id,
            request=request,
            status=AuditStatus.pending,
        )
        _jobs[audit_id] = job
        await self._queue.put(job)
        logger.info(f"Submitted audit job {audit_id}")
        return audit_id

    def get_job(self, audit_id: str) -> AuditJob | None:
        return get_job(audit_id)

    async def _worker_loop(self):
        """Background loop that picks up jobs and dispatches them."""
        while self._running:
            try:
                job = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                # Dispatch without blocking the worker loop
                asyncio.create_task(self._run_job(job))
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Worker loop error: {e}")

    async def _run_job(self, job: AuditJob):
        """Execute a single audit job with concurrency limiting."""
        async with self._semaphore:
            job.status = AuditStatus.running
            job.started_at = datetime.now(timezone.utc)
            logger.info(f"[{job.audit_id}] Running audit")

            try:
                if self._runner is None:
                    raise RuntimeError("No audit runner configured")

                report = await asyncio.wait_for(
                    self._runner(job),
                    timeout=settings.aegis_audit_timeout_seconds,
                )
                job.report = report
                job.status = AuditStatus.complete
                logger.info(
                    f"[{job.audit_id}] Completed — status={report.status}, "
                    f"findings={report.summary.total_findings}"
                )
            except asyncio.TimeoutError:
                job.status = AuditStatus.failed
                job.error = (
                    f"Audit timed out after {settings.aegis_audit_timeout_seconds}s"
                )
                logger.error(f"[{job.audit_id}] Timeout")
            except Exception as e:
                job.status = AuditStatus.failed
                job.error = str(e)
                logger.exception(f"[{job.audit_id}] Failed: {e}")
            finally:
                job.completed_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Singleton queue instance
# ---------------------------------------------------------------------------

audit_queue = AuditQueue()
