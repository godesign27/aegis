"""API contract tests for Aegis.

Tests validate:
- POST /v1/audits returns 202 with audit_id and poll_url
- GET /v1/audits/{id} returns the correct polling envelope
- GET /v1/audits/{id}/findings returns the correct findings shape
- GET /health returns { status: ok }
- Missing code in validation mode returns 422
- Unknown audit_id returns 404

NOTE: These tests mock the audit runner so they don't call Claude.
The runner is patched to return a deterministic synthetic report.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aegis.main import app
from aegis.models import (
    AuditJob,
    AuditReport,
    AuditStatus,
    BySeverity,
    ByDimension,
    Finding,
    ReportStatus,
    ReportSummary,
    Severity,
    Dimension,
    ToolType,
)


# ---------------------------------------------------------------------------
# Synthetic report factory
# ---------------------------------------------------------------------------


def _make_synthetic_report(audit_id: str) -> AuditReport:
    finding = Finding(
        id="finding_001",
        severity=Severity.high,
        dimension=Dimension.token_violation,
        rule="color.no-hardcoded-values",
        file="src/components/Button.tsx",
        line=14,
        code_snippet='className="bg-[#6366f1]"',
        violation="Hardcoded hex color in Tailwind arbitrary class.",
        expected="Use a Tailwind config-defined color class.",
        fix_suggestion="Replace 'bg-[#6366f1]' with 'bg-primary' or define the color in tailwind.config.js.",
        tool_pattern="bolt",
    )
    summary = ReportSummary(
        status=ReportStatus.blocked,
        total_findings=1,
        by_severity=BySeverity(high=1),
        by_dimension=ByDimension(token_violation=1),
        narrative=(
            "The AI tool generated a navigation component with a hardcoded hex color. "
            "One HIGH token violation was found. The output is blocked pending remediation."
        ),
    )
    return AuditReport(
        audit_id=audit_id,
        status=ReportStatus.blocked,
        tool_type=ToolType.bolt,
        policy_pack="boilerplate",
        created_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        findings=[finding],
        policy_pack_version="1.0.0",
        aegis_version="1.0.0",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Create a TestClient with the audit runner mocked.

    The mock runner immediately returns a synthetic report so tests don't
    make real Anthropic API calls or hit background task race conditions.
    """
    async def _mock_run_audit(job):
        return _make_synthetic_report(job.audit_id)

    # Patch before the lifespan starts so set_runner picks up the mock
    with patch("aegis.main.run_audit", new=_mock_run_audit):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


SAMPLE_CODE = {
    "src/components/Button.tsx": (
        'import React from "react";\n'
        'const Button = () => <button className="bg-[#6366f1] text-white px-4 py-2">Go</button>;\n'
        'export default Button;\n'
    )
}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Submit audit
# ---------------------------------------------------------------------------


class TestSubmitAudit:
    def test_submit_returns_202(self, client):
        payload = {
            "tool_type": "bolt",
            "policy_pack": "boilerplate",
            "code": SAMPLE_CODE,
        }
        response = client.post("/v1/audits", json=payload)
        assert response.status_code == 202

    def test_submit_returns_audit_id(self, client):
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        response = client.post("/v1/audits", json=payload)
        data = response.json()
        assert "audit_id" in data
        assert data["audit_id"].startswith("aud_")

    def test_submit_returns_poll_url(self, client):
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        response = client.post("/v1/audits", json=payload)
        data = response.json()
        assert "poll_url" in data
        assert data["poll_url"].startswith("/v1/audits/")

    def test_submit_returns_pending_status(self, client):
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        response = client.post("/v1/audits", json=payload)
        data = response.json()
        assert data["status"] == "pending"

    def test_submit_without_code_returns_422(self, client):
        """Validation mode requires code field."""
        payload = {"tool_type": "bolt", "mode": "validation"}
        response = client.post("/v1/audits", json=payload)
        assert response.status_code == 422

    def test_submit_comparison_without_repo_url_returns_422(self, client):
        """Comparison mode requires repo_url."""
        payload = {"tool_type": "bolt", "mode": "comparison"}
        response = client.post("/v1/audits", json=payload)
        assert response.status_code == 422

    def test_submit_infers_validation_mode_from_code(self, client):
        """If code is present, mode is inferred as validation."""
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        response = client.post("/v1/audits", json=payload)
        assert response.status_code == 202


# ---------------------------------------------------------------------------
# Poll audit
# ---------------------------------------------------------------------------


class TestPollAudit:
    def test_poll_unknown_id_returns_404(self, client):
        response = client.get("/v1/audits/aud_DOESNOTEXIST")
        assert response.status_code == 404

    def test_poll_pending_job_returns_pending(self, client):
        """Job should be pending immediately after submit (before runner processes it)."""
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        poll_resp = client.get(f"/v1/audits/{audit_id}")
        assert poll_resp.status_code == 200
        data = poll_resp.json()
        assert data["audit_id"] == audit_id
        assert data["status"] in ("pending", "running", "complete")

    def test_poll_response_schema(self, client):
        """Poll response must include audit_id and status fields."""
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        poll_resp = client.get(f"/v1/audits/{audit_id}")
        data = poll_resp.json()
        assert "audit_id" in data
        assert "status" in data

    def test_complete_job_includes_report(self, client):
        """When a job is complete, the poll response includes a report."""
        from aegis.queue import _jobs

        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        # Inject a synthetic complete report into the job store
        job = _jobs[audit_id]
        job.status = AuditStatus.complete
        job.report = _make_synthetic_report(audit_id)

        poll_resp = client.get(f"/v1/audits/{audit_id}")
        data = poll_resp.json()
        assert data["status"] == "complete"
        assert data["report"] is not None
        assert data["report"]["audit_id"] == audit_id

    def test_complete_report_has_aegis_version(self, client):
        """Report must always include aegis_version field."""
        from aegis.queue import _jobs

        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        job = _jobs[audit_id]
        job.status = AuditStatus.complete
        job.report = _make_synthetic_report(audit_id)

        poll_resp = client.get(f"/v1/audits/{audit_id}")
        report = poll_resp.json()["report"]
        assert report["aegis_version"] == "1.0.0"
        assert report["policy_pack_version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Findings endpoint
# ---------------------------------------------------------------------------


class TestFindingsEndpoint:
    def test_findings_unknown_id_returns_404(self, client):
        response = client.get("/v1/audits/aud_DOESNOTEXIST/findings")
        assert response.status_code == 404

    def test_findings_endpoint_returns_valid_shape(self, client):
        """Findings endpoint returns a valid shape regardless of job state.

        With the mock runner the job completes almost instantly, so we accept
        either an in-progress response (empty findings, no status) or a
        completed response (findings array present, status set).
        """
        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        findings_resp = client.get(f"/v1/audits/{audit_id}/findings")
        assert findings_resp.status_code == 200
        data = findings_resp.json()
        # Shape contract: these fields are always present
        assert "audit_id" in data
        assert "findings" in data
        assert isinstance(data["findings"], list)
        # audit_id echoed back correctly
        assert data["audit_id"] == audit_id

    def test_findings_complete_job_returns_findings(self, client):
        from aegis.queue import _jobs

        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        job = _jobs[audit_id]
        job.status = AuditStatus.complete
        job.report = _make_synthetic_report(audit_id)

        findings_resp = client.get(f"/v1/audits/{audit_id}/findings")
        data = findings_resp.json()
        assert data["audit_id"] == audit_id
        assert len(data["findings"]) == 1
        assert data["findings"][0]["severity"] == "HIGH"
        assert data["findings"][0]["rule"] == "color.no-hardcoded-values"
        assert data["status"] == "blocked"

    def test_findings_include_fix_suggestion(self, client):
        from aegis.queue import _jobs

        payload = {"tool_type": "bolt", "code": SAMPLE_CODE}
        submit_resp = client.post("/v1/audits", json=payload)
        audit_id = submit_resp.json()["audit_id"]

        job = _jobs[audit_id]
        job.status = AuditStatus.complete
        job.report = _make_synthetic_report(audit_id)

        findings_resp = client.get(f"/v1/audits/{audit_id}/findings")
        finding = findings_resp.json()["findings"][0]
        assert "fix_suggestion" in finding
        assert len(finding["fix_suggestion"]) > 10  # Must be non-trivial


# ---------------------------------------------------------------------------
# Report status logic
# ---------------------------------------------------------------------------


class TestReportStatusLogic:
    """Test the _compute_status function in isolation."""

    def test_high_finding_blocks(self):
        from aegis.agent import _compute_status

        findings = [
            Finding(
                id="f1",
                severity=Severity.high,
                dimension=Dimension.token_violation,
                rule="color.no-hardcoded-values",
                violation="hardcoded color",
                fix_suggestion="use token",
            )
        ]
        assert _compute_status(findings, "high") == ReportStatus.blocked

    def test_critical_finding_blocks_on_high_threshold(self):
        from aegis.agent import _compute_status

        findings = [
            Finding(
                id="f1",
                severity=Severity.critical,
                dimension=Dimension.hallucinated_component,
                rule="components.approved-packages",
                violation="non-existent package",
                fix_suggestion="remove import",
            )
        ]
        assert _compute_status(findings, "high") == ReportStatus.blocked

    def test_medium_finding_warns_on_high_threshold(self):
        from aegis.agent import _compute_status

        findings = [
            Finding(
                id="f1",
                severity=Severity.medium,
                dimension=Dimension.design_system_drift,
                rule="spacing.no-hardcoded-values",
                violation="inline spacing",
                fix_suggestion="use tailwind class",
            )
        ]
        assert _compute_status(findings, "high") == ReportStatus.warned

    def test_low_finding_passes_on_high_threshold(self):
        from aegis.agent import _compute_status

        findings = [
            Finding(
                id="f1",
                severity=Severity.low,
                dimension=Dimension.design_system_drift,
                rule="patterns.consistent-event-handlers",
                violation="naming inconsistency",
                fix_suggestion="rename handler",
            )
        ]
        assert _compute_status(findings, "high") == ReportStatus.passed

    def test_no_findings_passes(self):
        from aegis.agent import _compute_status
        assert _compute_status([], "high") == ReportStatus.passed

    def test_medium_blocks_when_fail_on_medium(self):
        from aegis.agent import _compute_status

        findings = [
            Finding(
                id="f1",
                severity=Severity.medium,
                dimension=Dimension.token_violation,
                rule="spacing.no-hardcoded-values",
                violation="inline spacing",
                fix_suggestion="use tailwind class",
            )
        ]
        assert _compute_status(findings, "medium") == ReportStatus.blocked

    def test_high_passes_when_fail_on_critical(self):
        from aegis.agent import _compute_status

        findings = [
            Finding(
                id="f1",
                severity=Severity.high,
                dimension=Dimension.token_violation,
                rule="color.no-hardcoded-values",
                violation="hardcoded color",
                fix_suggestion="use token",
            )
        ]
        # HIGH should NOT block when fail_on=critical
        assert _compute_status(findings, "critical") != ReportStatus.blocked
