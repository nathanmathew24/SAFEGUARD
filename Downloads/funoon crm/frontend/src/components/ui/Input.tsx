import { InputHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

export function Input({ label, error, className, id, ...props }: InputProps) {
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={id} className="block text-xs text-ink-500">
          {label}
        </label>
      )}
      <input
        id={id}
        className={cn(
          'w-full px-3 py-2 text-sm bg-white border rounded-md text-ink-800 placeholder-ink-400',
          'focus:outline-none focus:ring-1 focus:ring-ink-400 focus:border-ink-400 transition-colors',
          error ? 'border-status-red' : 'border-ink-200',
          className,
        )}
        {...props}
      />
      {error && <p className="text-xs text-status-red">{error}</p>}
    </div>
  )
}
