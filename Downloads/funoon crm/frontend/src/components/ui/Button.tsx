import { ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...props
}: ButtonProps) {
  const base = 'inline-flex items-center justify-center font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary:   'bg-ink-900 text-white hover:bg-ink-700',
    secondary: 'border border-ink-200 text-ink-600 bg-white hover:bg-ink-50',
    ghost:     'text-ink-600 hover:bg-ink-100 hover:text-ink-800',
    danger:    'bg-red-50 text-status-red border border-red-200 hover:bg-red-100',
  }

  const sizes = {
    sm: 'text-xs px-2.5 py-1',
    md: 'text-sm px-3 py-1.5',
  }

  return (
    <button className={cn(base, variants[variant], sizes[size], className)} {...props}>
      {children}
    </button>
  )
}
