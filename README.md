# Aegis — UI Governance API

**The control plane for AI-generated user interfaces.**

Aegis audits UI code produced by AI coding tools (Bolt.new, Lovable.dev, Figma Make)
against design system policy packs and returns structured, actionable findings.

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY

# 3. Start the service
uvicorn aegis.main:app --reload

# 4. Run tests
pytest tests/ -v
```

---

## API

### Submit an audit
```
POST /v1/audits
Content-Type: application/json

{
  "tool_type": "bolt",
  "policy_pack": "boilerplate",
  "code": {
    "src/components/Button.tsx": "<file content>"
  },
  "options": {
    "fail_on": "high"
  }
}

→ 202 Accepted
{ "audit_id": "aud_01HV5K...", "status": "pending", "poll_url": "/v1/audits/aud_01HV5K..." }
```

### Poll for results
```
GET /v1/audits/{audit_id}

→ 200 OK
{ "audit_id": "...", "status": "complete", "report": { ... } }
```

### Get findings only
```
GET /v1/audits/{audit_id}/findings
```

### Health check
```
GET /health → { "status": "ok", "version": "1.0.0" }
```

---

## Architecture

```
aegis/
├── main.py       — FastAPI routes
├── agent.py      — Claude agent loop (7-step audit workflow)
├── queue.py      — Async in-memory job queue (Redis-ready interface)
├── github.py     — GitHub API client for comparison mode
├── parser.py     — UI code normalizer (extracts tokens, components, ARIA)
├── models.py     — Pydantic request/response models
├── config.py     — Settings from environment variables
└── skill/        — Audit methodology (SKILL.md + reference docs)
```

### Two modes

- **Validation mode** — submit code directly, audited immediately against the policy pack
- **Comparison mode** — provide a GitHub repo URL; Aegis diffs baseline vs AI output, audits only changed files

### Audit dimensions

1. Token violations (hardcoded colors, spacing, typography)
2. Component violations (wrong imports, unapproved packages)
3. Accessibility regressions (ARIA drift, semantic HTML, keyboard nav)
4. Design system drift (pattern divergence from source repo)
5. Hallucinated components (non-existent packages, invented APIs)

### Report status

| Status | Meaning |
|---|---|
| `blocked` | CRITICAL or HIGH findings — do not merge |
| `warned` | MEDIUM findings only — review before merging |
| `passed` | LOW/INFO only — safe to ship |

The `options.fail_on` field controls the blocking threshold: `critical`, `high` (default), or `medium`.

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `GITHUB_TOKEN` | No* | GitHub token (*required for private repos) |
| `AEGIS_ENV` | No | `development` \| `production` |
| `AEGIS_LOG_LEVEL` | No | Log level (default: `INFO`) |
| `AEGIS_MAX_CONCURRENT_AUDITS` | No | Max parallel Claude calls (default: `5`) |
| `AEGIS_AUDIT_TIMEOUT_SECONDS` | No | Per-audit timeout (default: `120`) |

---

## Product notes

- **Layer 1 (this service)** — Core governance: validate code against policy packs
- **Layer 2 (future)** — Agentic pre-generation governance using Layer 1 as a constraint system
- **MCP server (future)** — `agent.py` is structured so `run_audit` can be called directly as a sync function for real-time IDE integration
- **Policy packs are the IP** — `boilerplate` covers Tailwind+React; future packs for Material Design, Radix, and company-specific systems
