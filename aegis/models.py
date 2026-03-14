"""Pydantic models for all Aegis API request and response shapes.

The report schema is a versioned contract — field names must not change
without a version bump and backward-compatibility period.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ToolType(str, Enum):
    bolt = "bolt"
    lovable = "lovable"
    figma_make = "figma-make"
    unknown = "unknown"


class PolicyPack(str, Enum):
    boilerplate = "boilerplate"
    custom = "custom"


class AuditMode(str, Enum):
    validation = "validation"
    comparison = "comparison"


class FailOn(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"


class AuditStatus(str, Enum):
    pending = "pending"
    running = "running"
    complete = "complete"
    failed = "failed"


class ReportStatus(str, Enum):
    blocked = "blocked"
    warned = "warned"
    passed = "passed"


class Severity(str, Enum):
    critical = "CRITICAL"
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"
    info = "INFO"


class Dimension(str, Enum):
    token_violation = "token_violation"
    component_violation = "component_violation"
    accessibility_regression = "accessibility_regression"
    design_system_drift = "design_system_drift"
    hallucinated_component = "hallucinated_component"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AuditOptions(BaseModel):
    include_info: bool = True
    fail_on: FailOn = FailOn.high


class AuditRequest(BaseModel):
    tool_type: ToolType = ToolType.unknown
    policy_pack: str = "boilerplate"  # str to allow custom pack names
    mode: AuditMode | None = None  # inferred if omitted
    # Validation mode: map of filepath → file content
    code: dict[str, str] | None = None
    # Comparison mode: GitHub source repo
    repo_url: str | None = None
    branch: str = "main"
    options: AuditOptions = Field(default_factory=AuditOptions)

    def inferred_mode(self) -> AuditMode:
        if self.mode:
            return self.mode
        if self.repo_url:
            return AuditMode.comparison
        return AuditMode.validation


# ---------------------------------------------------------------------------
# Finding model (the unit of audit output)
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    id: str
    severity: Severity
    dimension: Dimension
    rule: str
    file: str | None = None
    line: int | None = None
    code_snippet: str | None = None
    violation: str
    expected: str | None = None
    fix_suggestion: str
    tool_pattern: str | None = None


# ---------------------------------------------------------------------------
# Report models
# ---------------------------------------------------------------------------


class BySeverity(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ByDimension(BaseModel):
    token_violation: int = 0
    component_violation: int = 0
    accessibility_regression: int = 0
    design_system_drift: int = 0
    hallucinated_component: int = 0


class ReportSummary(BaseModel):
    status: ReportStatus
    total_findings: int
    by_severity: BySeverity
    by_dimension: ByDimension
    narrative: str


class DiffSummary(BaseModel):
    """Only present in comparison mode."""
    files_added: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    files_removed: list[str] = Field(default_factory=list)
    files_unchanged: int = 0


class AuditReport(BaseModel):
    audit_id: str
    status: ReportStatus
    tool_type: ToolType
    policy_pack: str
    created_at: str
    summary: ReportSummary
    findings: list[Finding]
    diff_summary: DiffSummary | None = None
    policy_pack_version: str = "1.0.0"
    aegis_version: str = "1.0.0"


# ---------------------------------------------------------------------------
# Job / queue models
# ---------------------------------------------------------------------------


class AuditJob(BaseModel):
    """Internal representation of a queued audit job."""
    audit_id: str
    request: AuditRequest
    status: AuditStatus = AuditStatus.pending
    report: AuditReport | None = None
    error: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ---------------------------------------------------------------------------
# API response envelopes
# ---------------------------------------------------------------------------


class SubmitResponse(BaseModel):
    audit_id: str
    status: AuditStatus
    poll_url: str


class PollResponse(BaseModel):
    audit_id: str
    status: AuditStatus
    report: AuditReport | None = None
    error: str | None = None


class FindingsResponse(BaseModel):
    audit_id: str
    status: ReportStatus | None = None
    findings: list[Finding] = Field(default_factory=list)
    summary: ReportSummary | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
