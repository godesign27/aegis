import { useState } from 'react'
import { runAudit } from './api'
import { SubmitForm } from './components/SubmitForm'
import { AuditProgress } from './components/AuditProgress'
import { AuditReport } from './components/AuditReport'

/**
 * App state machine:
 *   idle → loading (submitting + polling) → complete | failed → idle (reset)
 */
export function App() {
  const [phase, setPhase] = useState('idle') // idle | loading | complete | failed
  const [pollData, setPollData] = useState(null)
  const [report, setReport] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)

  const handleSubmit = async (payload) => {
    setPhase('loading')
    setPollData(null)
    setReport(null)
    setErrorMsg(null)

    try {
      const result = await runAudit(payload, (update) => {
        setPollData(update)
      })

      if (result.status === 'complete') {
        setReport(result.report)
        setPhase('complete')
      } else {
        setErrorMsg(result.error ?? 'Audit failed. Check the API server and try again.')
        setPhase('failed')
      }
    } catch (err) {
      setErrorMsg(err.message)
      setPhase('failed')
    }
  }

  const handleReset = () => {
    setPhase('idle')
    setPollData(null)
    setReport(null)
    setErrorMsg(null)
  }

  const auditId = pollData?.audit_id ?? null
  const pollAttempt = pollData?.attempt ?? 0

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">

      {/* ── Header ── */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          {/* Logo + wordmark */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
              </svg>
            </div>
            <div>
              <span className="text-sm font-semibold text-gray-900 tracking-tight">Aegis</span>
              <span className="ml-2 text-xs text-gray-400 font-medium hidden sm:inline">
                UI Governance
              </span>
            </div>
          </div>

          {/* Status pill */}
          <div className="flex items-center gap-3">
            {phase === 'loading' && (
              <span className="inline-flex items-center gap-1.5 text-xs text-amber-600 font-medium bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
                Auditing
              </span>
            )}
            {phase === 'complete' && (
              <span className="inline-flex items-center gap-1.5 text-xs text-emerald-600 font-medium bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Complete
              </span>
            )}
            <a
              href="https://github.com/godesign27/aegis"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost text-xs py-1.5 px-2.5"
            >
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              GitHub
            </a>
          </div>
        </div>
      </header>

      {/* ── Main layout ── */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-8 items-start">

          {/* ── Left panel: submission form ── */}
          <div className="lg:sticky lg:top-22">
            <div className="card px-6 py-5">
              {/* Panel header */}
              <div className="mb-5">
                <h1 className="text-base font-semibold text-gray-900">Submit audit</h1>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
                  Paste your AI-generated UI code. Aegis checks it against the
                  active policy pack and returns structured findings.
                </p>
              </div>

              <SubmitForm
                onSubmit={handleSubmit}
                isLoading={phase === 'loading'}
              />
            </div>

            {/* Tips card */}
            {phase === 'idle' && (
              <div className="mt-4 rounded-xl border border-gray-200 bg-brand-50 px-4 py-3">
                <p className="text-xs font-semibold text-brand-700 mb-2">Quick tips</p>
                <ul className="space-y-1.5 text-xs text-brand-600">
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0">→</span>
                    Paste one or more files. Use the <strong>Add file</strong> button for multi-file audits.
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0">→</span>
                    Select the AI tool that generated the code for better detection accuracy.
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="flex-shrink-0">→</span>
                    Audits take 30–60 seconds. Results are exportable as JSON.
                  </li>
                </ul>
              </div>
            )}
          </div>

          {/* ── Right panel: results ── */}
          <div className="min-w-0">
            {phase === 'idle' && (
              <EmptyState />
            )}
            {phase === 'loading' && (
              <AuditProgress auditId={auditId} attempt={pollAttempt} />
            )}
            {phase === 'failed' && (
              <ErrorState message={errorMsg} onReset={handleReset} />
            )}
            {phase === 'complete' && report && (
              <AuditReport report={report} onReset={handleReset} />
            )}
          </div>
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-gray-400">
          <span>Aegis UI Governance — Layer 1</span>
          <span>Powered by Claude</span>
        </div>
      </footer>
    </div>
  )
}

/* ── Supporting views ── */

function EmptyState() {
  return (
    <div className="card px-8 py-16 text-center animate-fade-in">
      <div className="w-16 h-16 rounded-2xl bg-brand-50 border border-brand-100 flex items-center justify-center mx-auto mb-5">
        <svg className="w-8 h-8 text-brand-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
      </div>
      <h2 className="text-base font-semibold text-gray-900 mb-2">
        No audit yet
      </h2>
      <p className="text-sm text-gray-500 max-w-xs mx-auto leading-relaxed">
        Paste your AI-generated UI code on the left and click{' '}
        <strong className="text-gray-700">Run audit</strong> to check it against
        the design system policy pack.
      </p>

      <div className="mt-8 grid grid-cols-3 gap-4 max-w-sm mx-auto">
        {[
          { icon: '🎨', label: 'Token violations', desc: 'Hardcoded colors, spacing, typography' },
          { icon: '♿', label: 'Accessibility', desc: 'ARIA drift, keyboard nav, semantic HTML' },
          { icon: '👻', label: 'Hallucinations', desc: 'Non-existent packages & components' },
        ].map(item => (
          <div key={item.label} className="text-center">
            <div className="text-2xl mb-1.5">{item.icon}</div>
            <p className="text-xs font-medium text-gray-700">{item.label}</p>
            <p className="text-[11px] text-gray-400 mt-0.5 leading-tight">{item.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function ErrorState({ message, onReset }) {
  return (
    <div className="card px-6 py-8 text-center animate-fade-in">
      <div className="text-3xl mb-3">❌</div>
      <h3 className="text-sm font-semibold text-gray-900 mb-2">Audit failed</h3>
      {message && (
        <p className="text-xs text-red-600 bg-red-50 border border-red-100 rounded-lg px-3 py-2 mb-4 font-mono text-left break-all">
          {message}
        </p>
      )}
      <p className="text-xs text-gray-400 mb-4">
        Make sure the Aegis API is running at{' '}
        <code className="font-mono bg-gray-100 px-1 rounded">localhost:8000</code>
        {' '}and your <code className="font-mono bg-gray-100 px-1 rounded">ANTHROPIC_API_KEY</code> is set.
      </p>
      <button onClick={onReset} className="btn-secondary text-sm">
        Try again
      </button>
    </div>
  )
}
