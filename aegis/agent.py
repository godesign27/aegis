"""Aegis Audit Agent — Claude-powered audit loop.

The agent reads the skill file + reference documents, then uses Claude
with tool_use to run the 7-step audit workflow defined in the skill.

Architecture note: `run_audit` is a plain async function so it can be called:
  a) from the job queue (async, background task) for the REST API
  b) directly as a synchronous-style call (with asyncio.run) for future MCP server use
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import anthropic

from aegis.config import settings
from aegis.models import (
    AuditJob,
    AuditMode,
    AuditReport,
    AuditStatus,
    BySeverity,
    ByDimension,
    DiffSummary,
    Dimension,
    Finding,
    ReportStatus,
    ReportSummary,
    Severity,
    ToolType,
)
from aegis.parser import parse_files

logger = logging.getLogger(__name__)

SKILL_DIR = Path(__file__).parent / "skill"

# ---------------------------------------------------------------------------
# Skill content loader
# ---------------------------------------------------------------------------


def _load_skill_content() -> str:
    """Load the main SKILL.md and all reference files into a single string."""
    parts: list[str] = []

    main_skill = SKILL_DIR / "SKILL.md"
    if main_skill.exists():
        parts.append(f"# SKILL.md\n\n{main_skill.read_text()}")

    refs_dir = SKILL_DIR / "references"
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob("*.md")):
            parts.append(f"\n\n---\n\n# {ref_file.name}\n\n{ref_file.read_text()}")

    return "\n".join(parts)


_SKILL_CONTENT: str | None = None


def get_skill_content() -> str:
    global _SKILL_CONTENT
    if _SKILL_CONTENT is None:
        _SKILL_CONTENT = _load_skill_content()
    return _SKILL_CONTENT


# ---------------------------------------------------------------------------
# Tool definitions for the Claude agent
# ---------------------------------------------------------------------------


def _build_tool_definitions() -> list[dict]:
    return [
        {
            "name": "read_policy_pack",
            "description": (
                "Read the content of a named policy pack. Returns the full policy rules "
                "as a string. Use 'boilerplate' for the default Tailwind+React policy pack."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Policy pack name: 'boilerplate' or a custom pack name",
                    }
                },
                "required": ["name"],
            },
        },
        {
            "name": "read_tool_profile",
            "description": (
                "Read tool-specific behavioral heuristics for a given AI coding tool. "
                "Returns detection patterns and severity adjustments specific to that tool."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool_type": {
                        "type": "string",
                        "enum": ["bolt", "lovable", "figma-make", "unknown"],
                        "description": "The AI tool that generated the UI code",
                    }
                },
                "required": ["tool_type"],
            },
        },
        {
            "name": "read_parsed_code",
            "description": (
                "Get the pre-parsed summary of the submitted UI code files. "
                "Returns extracted colors, spacing, typography, components, imports, and ARIA attributes."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "get_raw_file",
            "description": (
                "Get the raw source content of a specific file from the submitted code. "
                "Use this to inspect a file in detail before generating a finding."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "The file path as submitted in the audit request",
                    }
                },
                "required": ["filepath"],
            },
        },
        {
            "name": "submit_findings",
            "description": (
                "Submit the final audit findings. Call this once when the audit is complete. "
                "Pass ALL findings discovered across all five dimensions. "
                "Each finding must include: id, severity, dimension, rule, violation, fix_suggestion. "
                "Also pass a narrative summary and the overall status."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "findings": {
                        "type": "array",
                        "description": "Array of finding objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "severity": {
                                    "type": "string",
                                    "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
                                },
                                "dimension": {
                                    "type": "string",
                                    "enum": [
                                        "token_violation",
                                        "component_violation",
                                        "accessibility_regression",
                                        "design_system_drift",
                                        "hallucinated_component",
                                    ],
                                },
                                "rule": {"type": "string"},
                                "file": {"type": "string"},
                                "line": {"type": "integer"},
                                "code_snippet": {"type": "string"},
                                "violation": {"type": "string"},
                                "expected": {"type": "string"},
                                "fix_suggestion": {"type": "string"},
                                "tool_pattern": {"type": "string"},
                            },
                            "required": [
                                "id",
                                "severity",
                                "dimension",
                                "rule",
                                "violation",
                                "fix_suggestion",
                            ],
                        },
                    },
                    "narrative": {
                        "type": "string",
                        "description": (
                            "2-4 sentence executive summary: what the AI did overall, "
                            "the most significant governance concern, and whether safe to ship."
                        ),
                    },
                },
                "required": ["findings", "narrative"],
            },
        },
    ]


# ---------------------------------------------------------------------------
# Tool handler
# ---------------------------------------------------------------------------


class ToolHandler:
    def __init__(self, job: AuditJob, github_client=None):
        self.job = job
        self.github_client = github_client
        self._parsed_code: list | None = None
        self._final_findings: list[dict] | None = None
        self._narrative: str = ""

    def _get_parsed_code(self):
        if self._parsed_code is None and self.job.request.code:
            self._parsed_code = parse_files(self.job.request.code)
        return self._parsed_code

    def handle(self, tool_name: str, tool_input: dict) -> str:
        if tool_name == "read_policy_pack":
            return self._read_policy_pack(tool_input["name"])
        elif tool_name == "read_tool_profile":
            return self._read_tool_profile(tool_input["tool_type"])
        elif tool_name == "read_parsed_code":
            return self._read_parsed_code()
        elif tool_name == "get_raw_file":
            return self._get_raw_file(tool_input["filepath"])
        elif tool_name == "submit_findings":
            self._final_findings = tool_input["findings"]
            self._narrative = tool_input.get("narrative", "")
            return json.dumps({"status": "findings_received", "count": len(self._final_findings)})
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    def _read_policy_pack(self, name: str) -> str:
        policy_file = SKILL_DIR / "references" / "policy-pack-boilerplate.md"
        if name == "boilerplate" and policy_file.exists():
            return policy_file.read_text()
        # If a custom pack was passed inline, return it
        return f"Policy pack '{name}' not found. Using boilerplate rules."

    def _read_tool_profile(self, tool_type: str) -> str:
        profile_file = SKILL_DIR / "references" / "tool-profiles.md"
        if profile_file.exists():
            content = profile_file.read_text()
            # Extract only the relevant tool section
            tool_map = {
                "bolt": "## Bolt.new",
                "lovable": "## Lovable.dev",
                "figma-make": "## Figma Make",
            }
            marker = tool_map.get(tool_type)
            if marker and marker in content:
                start = content.index(marker)
                # Find the next ## section or end of file
                next_section = content.find("\n## ", start + 1)
                section = content[start:next_section] if next_section != -1 else content[start:]
                return section
        return f"No tool profile found for '{tool_type}'."

    def _read_parsed_code(self) -> str:
        parsed = self._get_parsed_code()
        if not parsed:
            return json.dumps({"error": "No code submitted for parsing."})
        result = []
        for pf in parsed:
            result.append({
                "filepath": pf.filepath,
                "hex_colors": pf.hex_colors,
                "rgb_colors": pf.rgb_colors,
                "hsl_colors": pf.hsl_colors,
                "named_colors": pf.named_colors,
                "tailwind_arbitrary_colors": pf.tailwind_arbitrary_colors,
                "inline_spacing": pf.inline_spacing,
                "tailwind_arbitrary_spacing": pf.tailwind_arbitrary_spacing,
                "inline_typography": pf.inline_typography,
                "tailwind_arbitrary_typography": pf.tailwind_arbitrary_typography,
                "import_statements": pf.import_statements,
                "component_names": pf.component_names,
                "aria_attributes": pf.aria_attributes,
                "semantic_elements": pf.semantic_elements,
                "click_handlers_count": len(pf.click_handlers),
                "keyboard_handlers_count": len(pf.keyboard_handlers),
                "img_tags": pf.img_tags,
            })
        return json.dumps(result, indent=2)

    def _get_raw_file(self, filepath: str) -> str:
        if self.job.request.code and filepath in self.job.request.code:
            return self.job.request.code[filepath]
        return f"File '{filepath}' not found in submitted code."


# ---------------------------------------------------------------------------
# Core audit runner
# ---------------------------------------------------------------------------


async def run_audit(job: AuditJob, github_client=None) -> AuditReport:
    """
    Run the full 7-step audit workflow using Claude.

    This is the core function that can be called:
    - from the queue (async background task)
    - directly (future MCP synchronous use)
    """
    skill_content = get_skill_content()
    tool_defs = _build_tool_definitions()
    handler = ToolHandler(job, github_client)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    mode = job.request.inferred_mode()
    tool_type = job.request.tool_type.value

    system_prompt = f"""You are the Aegis audit agent. You follow the exact 7-step workflow
defined in the skill file below. Your job is to evaluate AI-generated UI code against the
active policy pack and produce structured, actionable audit findings.

SKILL CONTENT:
{skill_content}

AUDIT CONTEXT:
- Audit ID: {job.audit_id}
- Tool type: {tool_type}
- Policy pack: {job.request.policy_pack}
- Mode: {mode.value}
- Files submitted: {list(job.request.code.keys()) if job.request.code else 'none (comparison mode)'}

Follow the 7-step workflow. Use the provided tools to read the policy pack, tool profile,
parsed code summary, and raw file content. When you have completed all five validation
dimensions, call submit_findings with ALL findings and a narrative.

Remember the behavioral rules:
- Never invent violations. Only flag what you are certain about.
- Always quote exact code in code_snippet (max 120 chars).
- Always provide a concrete, specific fix suggestion.
- Assign sequential finding IDs: finding_001, finding_002, etc.
"""

    user_message = (
        f"Please run a full audit of the submitted UI code. "
        f"Tool type is '{tool_type}'. Policy pack is '{job.request.policy_pack}'. "
        f"Mode is '{mode.value}'. "
        f"Start by reading the policy pack and tool profile, then read the parsed code summary, "
        f"inspect individual files as needed, and call submit_findings when complete."
    )

    messages = [{"role": "user", "content": user_message}]

    logger.info(f"[{job.audit_id}] Starting Claude agent loop")

    # Agent loop — runs until Claude stops calling tools
    max_iterations = 20
    for iteration in range(max_iterations):
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=8192,
            system=system_prompt,
            tools=tool_defs,
            messages=messages,
        )

        logger.debug(f"[{job.audit_id}] Iteration {iteration}: stop_reason={response.stop_reason}")

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            logger.info(f"[{job.audit_id}] Agent finished (end_turn)")
            break

        if response.stop_reason != "tool_use":
            logger.warning(f"[{job.audit_id}] Unexpected stop_reason: {response.stop_reason}")
            break

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            logger.info(f"[{job.audit_id}] Tool call: {block.name}")
            result = handler.handle(block.name, block.input)

            # If findings submitted, we can stop after this round
            if block.name == "submit_findings":
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
                messages.append({"role": "user", "content": tool_results})
                logger.info(f"[{job.audit_id}] Findings submitted — stopping agent loop")
                # One more pass to let Claude acknowledge, but we'll stop after
                break

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

        # If findings were submitted, exit the loop
        if handler._final_findings is not None:
            break

    # ---------------------------------------------------------------------------
    # Build the structured report from whatever findings were collected
    # ---------------------------------------------------------------------------
    return _build_report(job, handler)


def _compute_status(findings: list[Finding], fail_on: str) -> ReportStatus:
    """Determine the overall report status based on the fail_on threshold."""
    severity_order = {
        Severity.critical: 4,
        Severity.high: 3,
        Severity.medium: 2,
        Severity.low: 1,
        Severity.info: 0,
    }
    threshold_map = {
        "critical": 4,
        "high": 3,
        "medium": 2,
    }
    threshold = threshold_map.get(fail_on, 3)

    for finding in findings:
        if severity_order.get(finding.severity, 0) >= threshold:
            return ReportStatus.blocked

    # Check if any MEDIUM (warn)
    for finding in findings:
        if finding.severity == Severity.medium:
            return ReportStatus.warned

    return ReportStatus.passed


def _build_report(job: AuditJob, handler: ToolHandler) -> AuditReport:
    """Assemble the final AuditReport from collected findings."""
    from datetime import datetime, timezone

    raw_findings = handler._final_findings or []
    narrative = handler._narrative or "Audit completed with no findings submitted."

    # Parse findings into typed models
    findings: list[Finding] = []
    for i, raw in enumerate(raw_findings, start=1):
        try:
            findings.append(Finding(
                id=raw.get("id", f"finding_{i:03d}"),
                severity=Severity(raw.get("severity", "LOW")),
                dimension=Dimension(raw.get("dimension", "token_violation")),
                rule=raw.get("rule", "unknown"),
                file=raw.get("file"),
                line=raw.get("line"),
                code_snippet=raw.get("code_snippet"),
                violation=raw.get("violation", ""),
                expected=raw.get("expected"),
                fix_suggestion=raw.get("fix_suggestion", ""),
                tool_pattern=raw.get("tool_pattern"),
            ))
        except Exception as e:
            logger.warning(f"Could not parse finding {i}: {e}")

    # Filter INFO findings if not requested
    if not job.request.options.include_info:
        findings = [f for f in findings if f.severity != Severity.info]

    # Compute aggregates
    by_severity = BySeverity(
        critical=sum(1 for f in findings if f.severity == Severity.critical),
        high=sum(1 for f in findings if f.severity == Severity.high),
        medium=sum(1 for f in findings if f.severity == Severity.medium),
        low=sum(1 for f in findings if f.severity == Severity.low),
        info=sum(1 for f in findings if f.severity == Severity.info),
    )
    by_dimension = ByDimension(
        token_violation=sum(1 for f in findings if f.dimension == Dimension.token_violation),
        component_violation=sum(1 for f in findings if f.dimension == Dimension.component_violation),
        accessibility_regression=sum(1 for f in findings if f.dimension == Dimension.accessibility_regression),
        design_system_drift=sum(1 for f in findings if f.dimension == Dimension.design_system_drift),
        hallucinated_component=sum(1 for f in findings if f.dimension == Dimension.hallucinated_component),
    )

    fail_on = job.request.options.fail_on.value
    status = _compute_status(findings, fail_on)

    summary = ReportSummary(
        status=status,
        total_findings=len(findings),
        by_severity=by_severity,
        by_dimension=by_dimension,
        narrative=narrative,
    )

    return AuditReport(
        audit_id=job.audit_id,
        status=status,
        tool_type=job.request.tool_type,
        policy_pack=job.request.policy_pack,
        created_at=datetime.now(timezone.utc).isoformat(),
        summary=summary,
        findings=findings,
        policy_pack_version="1.0.0",
        aegis_version="1.0.0",
    )
