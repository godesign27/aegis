import { useState } from 'react'

const TOOL_OPTIONS = [
  { value: 'bolt',       label: 'Bolt.new' },
  { value: 'lovable',    label: 'Lovable.dev' },
  { value: 'figma-make', label: 'Figma Make' },
  { value: 'unknown',    label: 'Unknown / other' },
]

const FAIL_ON_OPTIONS = [
  { value: 'critical', label: 'Critical only' },
  { value: 'high',     label: 'High+ (recommended)' },
  { value: 'medium',   label: 'Medium+' },
]

function FileEntry({ file, index, onChange, onRemove, canRemove }) {
  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
      {/* File name row */}
      <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 border-b border-gray-200">
        <svg className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <input
          type="text"
          value={file.name}
          onChange={e => onChange(index, 'name', e.target.value)}
          placeholder="src/components/Button.tsx"
          className="flex-1 bg-transparent text-xs font-mono text-gray-600 placeholder:text-gray-400
                     focus:outline-none min-w-0"
          spellCheck={false}
        />
        {canRemove && (
          <button
            onClick={() => onRemove(index)}
            className="text-gray-400 hover:text-red-500 transition-colors p-0.5 rounded"
            title="Remove file"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Code textarea */}
      <textarea
        value={file.content}
        onChange={e => onChange(index, 'content', e.target.value)}
        placeholder={`// Paste your ${file.name || 'component'} code here…`}
        rows={8}
        spellCheck={false}
        className="w-full px-3 py-2.5 font-mono text-xs text-gray-700 placeholder:text-gray-400/70
                   resize-y bg-white focus:outline-none leading-relaxed"
      />
    </div>
  )
}

export function SubmitForm({ onSubmit, isLoading }) {
  const [files, setFiles] = useState([{ name: '', content: '' }])
  const [toolType, setToolType] = useState('unknown')
  const [policyPack, setPolicyPack] = useState('boilerplate')
  const [failOn, setFailOn] = useState('high')
  const [includeInfo, setIncludeInfo] = useState(true)
  const [error, setError] = useState(null)

  const handleFileChange = (index, field, value) => {
    setFiles(prev => prev.map((f, i) => i === index ? { ...f, [field]: value } : f))
  }

  const addFile = () => setFiles(prev => [...prev, { name: '', content: '' }])

  const removeFile = (index) => setFiles(prev => prev.filter((_, i) => i !== index))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Build the code map: { filepath: content }
    const code = {}
    for (const file of files) {
      if (!file.content.trim()) {
        setError('At least one file must have content.')
        return
      }
      const name = file.name.trim() || `file_${Object.keys(code).length + 1}.tsx`
      code[name] = file.content
    }

    const payload = {
      tool_type: toolType,
      policy_pack: policyPack,
      code,
      options: { fail_on: failOn, include_info: includeInfo },
    }

    try {
      await onSubmit(payload)
    } catch (err) {
      setError(err.message)
    }
  }

  const hasContent = files.some(f => f.content.trim().length > 0)

  return (
    <form onSubmit={handleSubmit} className="space-y-5">

      {/* Code files */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="form-label mb-0">Code files</label>
          <button
            type="button"
            onClick={addFile}
            className="btn-ghost text-xs py-1 px-2"
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            Add file
          </button>
        </div>

        <div className="space-y-2">
          {files.map((file, i) => (
            <FileEntry
              key={i}
              file={file}
              index={i}
              onChange={handleFileChange}
              onRemove={removeFile}
              canRemove={files.length > 1}
            />
          ))}
        </div>
      </div>

      {/* Tool type + policy pack */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="form-label">AI tool</label>
          <select
            value={toolType}
            onChange={e => setToolType(e.target.value)}
            className="form-select"
          >
            {TOOL_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="form-label">Policy pack</label>
          <input
            type="text"
            value={policyPack}
            onChange={e => setPolicyPack(e.target.value)}
            className="form-input"
            placeholder="boilerplate"
          />
        </div>
      </div>

      {/* Options row */}
      <div className="flex items-center gap-4 pt-1">
        <div className="flex-1">
          <label className="form-label text-xs">Block threshold</label>
          <select
            value={failOn}
            onChange={e => setFailOn(e.target.value)}
            className="form-select text-xs py-1.5"
          >
            {FAIL_ON_OPTIONS.map(opt => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2 pt-5">
          <input
            type="checkbox"
            id="include-info"
            checked={includeInfo}
            onChange={e => setIncludeInfo(e.target.checked)}
            className="w-4 h-4 text-brand-600 border-gray-300 rounded focus:ring-brand-500"
          />
          <label htmlFor="include-info" className="text-sm text-gray-600 cursor-pointer select-none">
            Include INFO
          </label>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2.5 text-sm text-red-700 flex items-start gap-2">
          <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {error}
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={isLoading || !hasContent}
        className="btn-primary w-full justify-center py-2.5"
      >
        {isLoading ? (
          <>
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Running audit…
          </>
        ) : (
          <>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
            Run audit
          </>
        )}
      </button>
    </form>
  )
}
