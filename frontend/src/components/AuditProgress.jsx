/** Loading/polling state shown while the audit is running. */
export function AuditProgress({ auditId, attempt }) {
  const steps = [
    { label: 'Submitted', done: true },
    { label: 'Loading policy pack & tool profile', done: attempt >= 1 },
    { label: 'Parsing code files', done: attempt >= 2 },
    { label: 'Running 5 validation dimensions', done: attempt >= 4 },
    { label: 'Generating findings', done: false },
  ]

  return (
    <div className="card px-6 py-8 text-center animate-fade-in">
      {/* Spinner */}
      <div className="flex justify-center mb-6">
        <div className="relative w-12 h-12">
          <div className="absolute inset-0 rounded-full border-2 border-gray-100" />
          <div className="absolute inset-0 rounded-full border-2 border-brand-500 border-t-transparent animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <svg className="w-5 h-5 text-brand-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
        </div>
      </div>

      <h3 className="text-sm font-semibold text-gray-900 mb-1">Audit in progress</h3>
      {auditId && (
        <p className="font-mono text-[11px] text-gray-400 mb-6">{auditId}</p>
      )}

      {/* Progress steps */}
      <div className="text-left space-y-2 max-w-xs mx-auto">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center gap-3">
            <div className={`
              w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0
              ${step.done ? 'bg-brand-600' : 'bg-gray-100 border border-gray-200'}
            `}>
              {step.done ? (
                <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
              )}
            </div>
            <span className={`text-xs ${step.done ? 'text-gray-700 font-medium' : 'text-gray-400'}`}>
              {step.label}
            </span>
          </div>
        ))}
      </div>

      <p className="mt-6 text-xs text-gray-400">
        Deep audits take 30–60 seconds. Hang tight.
      </p>
    </div>
  )
}
