/**
 * Aegis API client.
 * Vite's dev proxy forwards /v1 → http://localhost:8000
 * In production, serve the built frontend from FastAPI at the same origin.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

/** Submit a new audit job. Returns { audit_id, status, poll_url }. */
export async function submitAudit(payload) {
  return request('/v1/audits', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

/** Poll an audit by ID. Returns { audit_id, status, report?, error? }. */
export async function pollAudit(auditId) {
  return request(`/v1/audits/${auditId}`)
}

/** Health check. Returns { status, version }. */
export async function checkHealth() {
  return request('/health')
}

/**
 * Submit an audit then poll until complete or failed.
 *
 * @param {object} payload   - AuditRequest body
 * @param {function} onUpdate - called with each poll response
 * @returns {Promise<object>} - final poll response
 */
export async function runAudit(payload, onUpdate) {
  const submit = await submitAudit(payload)
  onUpdate({ ...submit, phase: 'submitted' })

  // Progressive polling: start fast, slow down after a few seconds
  const delays = [1000, 1500, 2000, 2500, 3000, 4000, 5000]
  let attempt = 0

  while (true) {
    const delay = delays[Math.min(attempt, delays.length - 1)]
    await new Promise((r) => setTimeout(r, delay))

    const data = await pollAudit(submit.audit_id)
    onUpdate({ ...data, phase: 'polling', attempt })

    if (data.status === 'complete' || data.status === 'failed') {
      return data
    }
    attempt++
  }
}
