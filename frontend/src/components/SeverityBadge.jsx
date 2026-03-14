/**
 * SeverityBadge — compact pill showing a finding's severity level.
 * Size variants: 'sm' (default) and 'lg'.
 */

const SEVERITY_CONFIG = {
  CRITICAL: {
    bg: 'bg-red-100',
    text: 'text-red-700',
    dot: 'bg-red-500',
    border: 'border-red-200',
  },
  HIGH: {
    bg: 'bg-red-50',
    text: 'text-red-600',
    dot: 'bg-red-400',
    border: 'border-red-100',
  },
  MEDIUM: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    dot: 'bg-amber-400',
    border: 'border-amber-100',
  },
  LOW: {
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    dot: 'bg-blue-400',
    border: 'border-blue-100',
  },
  INFO: {
    bg: 'bg-gray-100',
    text: 'text-gray-500',
    dot: 'bg-gray-400',
    border: 'border-gray-200',
  },
}

export function SeverityBadge({ severity, size = 'sm' }) {
  const config = SEVERITY_CONFIG[severity] ?? SEVERITY_CONFIG.INFO
  const textSize = size === 'lg' ? 'text-xs' : 'text-[11px]'
  const padding = size === 'lg' ? 'px-2.5 py-1' : 'px-2 py-0.5'

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-medium rounded-full border
        ${config.bg} ${config.text} ${config.border} ${textSize} ${padding}
      `}
    >
      <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${config.dot}`} />
      {severity}
    </span>
  )
}

/** Count pills for the summary bar */
export function SeverityCount({ severity, count }) {
  if (count === 0) return null
  const config = SEVERITY_CONFIG[severity] ?? SEVERITY_CONFIG.INFO
  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold border
        ${config.bg} ${config.text} ${config.border}
      `}
    >
      {count} {severity}
    </span>
  )
}
