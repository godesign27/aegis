import { useState } from 'react'
import { SeverityBadge } from './SeverityBadge'
import { CodeBlock } from './CodeBlock'

const DIMENSION_LABELS = {
  token_violation: 'Token',
  component_violation: 'Component',
  accessibility_regression: 'Accessibility',
  design_system_drift: 'Drift',
  hallucinated_component: 'Hallucination',
}

const DIMENSION_COLORS = {
  token_violation: 'text-purple-600 bg-purple-50 border-purple-100',
  component_violation: 'text-blue-600 bg-blue-50 border-blue-100',
  accessibility_regression: 'text-orange-600 bg-orange-50 border-orange-100',
  design_system_drift: 'text-cyan-600 bg-cyan-50 border-cyan-100',
  hallucinated_component: 'text-rose-600 bg-rose-50 border-rose-100',
}

/** Left accent bar color by severity */
const ACCENT_COLORS = {
  CRITICAL: 'bg-red-500',
  HIGH: 'bg-red-400',
  MEDIUM: 'bg-amber-400',
  LOW: 'bg-blue-400',
  INFO: 'bg-gray-300',
}

export function FindingCard({ finding, index }) {
  const [open, setOpen] = useState(false)

  const dimLabel = DIMENSION_LABELS[finding.dimension] ?? finding.dimension
  const dimColor = DIMENSION_COLORS[finding.dimension] ?? 'text-gray-600 bg-gray-50 border-gray-200'
  const accentColor = ACCENT_COLORS[finding.severity] ?? 'bg-gray-300'

  return (
    <div className="card overflow-hidden animate-slide-up" style={{ animationDelay: `${index * 40}ms` }}>
      {/* Left severity accent bar */}
      <div className="flex">
        <div className={`w-1 flex-shrink-0 ${accentColor}`} />
        <div className="flex-1 min-w-0">

          {/* Header row — always visible */}
          <button
            onClick={() => setOpen(!open)}
            className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-gray-50/60 transition-colors"
          >
            <div className="flex items-center gap-2 flex-shrink-0 mt-0.5">
              <SeverityBadge severity={finding.severity} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                {/* Dimension tag */}
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-md border ${dimColor}`}>
                  {dimLabel}
                </span>
                {/* Rule */}
                <span className="font-mono text-xs text-gray-500 truncate">{finding.rule}</span>
              </div>

              {/* Violation summary */}
              <p className="mt-1 text-sm text-gray-700 leading-snug">
                {finding.violation}
              </p>

              {/* File + line */}
              {finding.file && (
                <p className="mt-1 font-mono text-[11px] text-gray-400 truncate">
                  {finding.file}
                  {finding.line ? `:${finding.line}` : ''}
                </p>
              )}
            </div>

            {/* Expand chevron */}
            <svg
              className={`flex-shrink-0 w-4 h-4 text-gray-400 mt-0.5 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Expanded detail */}
          {open && (
            <div className="px-4 pb-4 border-t border-gray-100 space-y-3 animate-fade-in">

              {/* Code snippet */}
              {finding.code_snippet && (
                <div className="mt-3">
                  <CodeBlock code={finding.code_snippet} label="Offending code" />
                </div>
              )}

              {/* Expected */}
              {finding.expected && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Expected</p>
                  <p className="text-sm text-gray-700">{finding.expected}</p>
                </div>
              )}

              {/* Fix suggestion — highlighted */}
              <div className="rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2.5">
                <p className="text-xs font-semibold text-emerald-700 mb-1 flex items-center gap-1">
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  Fix
                </p>
                <p className="text-sm text-emerald-800">{finding.fix_suggestion}</p>
              </div>

              {/* Tool pattern */}
              {finding.tool_pattern && (
                <p className="text-[11px] text-gray-400">
                  Pattern introduced by: <span className="font-medium text-gray-500">{finding.tool_pattern}</span>
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
