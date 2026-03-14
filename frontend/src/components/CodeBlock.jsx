import { useState } from 'react'

/** Monospace code display with optional copy-to-clipboard. */
export function CodeBlock({ code, label, className = '' }) {
  const [copied, setCopied] = useState(false)

  if (!code) return null

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Fallback: select and copy
    }
  }

  return (
    <div className={`relative group rounded-lg overflow-hidden border border-gray-100 ${className}`}>
      {label && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-gray-50 border-b border-gray-100">
          <span className="text-[11px] font-medium text-gray-400 uppercase tracking-wide">
            {label}
          </span>
          <button
            onClick={handleCopy}
            className="text-[11px] text-gray-400 hover:text-gray-600 transition-colors"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      )}
      {!label && (
        <button
          onClick={handleCopy}
          className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity
                     text-[11px] text-gray-400 hover:text-gray-600 bg-white px-2 py-1 rounded border border-gray-200 shadow-sm"
        >
          {copied ? '✓' : 'Copy'}
        </button>
      )}
      <pre className="code-block rounded-none border-0 m-0 text-gray-700 whitespace-pre-wrap break-all">
        <code>{code}</code>
      </pre>
    </div>
  )
}
