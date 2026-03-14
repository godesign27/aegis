import { useState } from 'react'
import { FindingCard } from './FindingCard'
import { SeverityCount } from './SeverityBadge'

const STATUS_CONFIG = {
  blocked: {
    icon: '⛔',
    label: 'Blocked',
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-700',
    headingText: 'text-red-800',
    desc: 'Critical or high-severity findings must be resolved before merging.',
  },
  warned: {
    icon: '⚠️',
    label: 'Warned',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    text: 'text-amber-700',
    headingText: 'text-amber-800',
    desc: 'Medium-severity findings detected. Review before merging.',
  },
  passed: {
    icon: '✅',
    label: 'Passed',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    text: 'text-emerald-700',
    headingText: 'text-emerald-800',
    desc: 'No blocking issues found. Safe to ship.',
  },
}

const DIMENSION_ORDER = [
  'token_violation',
  'component_violation',
  'hallucinated_component',
  'accessibility_regression',
  'design_system_drift',
]

const SEVERITY_ORDER = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']

function sortFindings(findings) {
  return [...findings].sort((a, b) => {
    const si = SEVERITY_ORDER.indexOf(a.severity)
    const sj = SEVERITY_ORDER.indexOf(b.severity)
    if (si !== sj) return si - sj
    const di = DIMENSION_ORDER.indexOf(a.dimension)
    const dj = DIMENSION_ORDER.indexOf(b.dimension)
    return di - dj
  })
}

export function AuditReport({ report, onReset }) {
  const [filter, setFilter] = useState('all')
  const status = report.status
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.passed
  const { summary, findings } = report

  const sorted = sortFindings(findings)
  const filtered = filter === 'all' ? sorted : sorted.filter(f => f.severity === filter)

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `aegis-report-${report.audit_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4 animate-fade-in">

      {/* Status banner */}
      <div className={`rounded-xl border px-5 py-4 ${config.bg} ${config.border}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">{config.icon}</span>
              <h2 className={`text-lg font-semibold ${config.headingText}`}>
                {config.label}
              </h2>
              <span className={`text-sm ${config.text} font-medium`}>
                — {summary.total_findings} finding{summary.total_findings !== 1 ? 's' : ''}
              </span>
            </div>
            <p className={`text-sm ${config.text} mb-3`}>{config.desc}</p>

            {/* Severity counts */}
            <div className="flex flex-wrap gap-1.5">
              <SeverityCount severity="CRITICAL" count={summary.by_severity.critical} />
              <SeverityCount severity="HIGH"     count={summary.by_severity.high} />
              <SeverityCount severity="MEDIUM"   count={summary.by_severity.medium} />
              <SeverityCount severity="LOW"      count={summary.by_severity.low} />
              <SeverityCount severity="INFO"     count={summary.by_severity.info} />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 flex-shrink-0">
            <button onClick={handleExport} className="btn-secondary text-xs py-1.5 px-3">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export JSON
            </button>
            <button onClick={onReset} className="btn-secondary text-xs py-1.5 px-3">
              New audit
            </button>
          </div>
        </div>

        {/* Narrative */}
        {summary.narrative && (
          <p className={`mt-3 pt-3 border-t ${config.border} text-sm ${config.text} leading-relaxed`}>
            {summary.narrative}
          </p>
        )}
      </div>

      {/* Meta row */}
      <div className="flex items-center justify-between text-xs text-gray-400 px-1">
        <div className="flex items-center gap-3">
          <span>ID: <span className="font-mono">{report.audit_id}</span></span>
          <span>·</span>
          <span>Tool: <span className="font-medium text-gray-600">{report.tool_type}</span></span>
          <span>·</span>
          <span>Policy: <span className="font-medium text-gray-600">{report.policy_pack}</span></span>
        </div>
        <span>Aegis v{report.aegis_version}</span>
      </div>

      {/* Findings list */}
      {findings.length > 0 ? (
        <div className="space-y-2">
          {/* Filter tabs */}
          <div className="flex items-center gap-1 overflow-x-auto pb-1">
            {['all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map(f => {
              const count = f === 'all'
                ? findings.length
                : findings.filter(x => x.severity === f).length
              if (count === 0 && f !== 'all') return null
              return (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`
                    flex-shrink-0 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors
                    ${filter === f
                      ? 'bg-brand-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'}
                  `}
                >
                  {f === 'all' ? 'All' : f} ({count})
                </button>
              )
            })}
          </div>

          {/* Finding cards */}
          <div className="space-y-2">
            {filtered.map((finding, i) => (
              <FindingCard key={finding.id} finding={finding} index={i} />
            ))}
          </div>
        </div>
      ) : (
        <div className="card px-6 py-8 text-center text-gray-400">
          <div className="text-3xl mb-2">✨</div>
          <p className="text-sm font-medium text-gray-600">No findings</p>
          <p className="text-xs mt-1">The audit completed with no policy violations detected.</p>
        </div>
      )}
    </div>
  )
}
