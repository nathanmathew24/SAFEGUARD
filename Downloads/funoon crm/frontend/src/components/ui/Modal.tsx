import { useEffect } from 'react'
import { cn } from '../../lib/utils'

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  className?: string
}

export function Modal({ open, onClose, title, children, className }: ModalProps) {
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-ink-900/40"
        onClick={onClose}
      />
      <div
        className={cn(
          'relative bg-white border border-ink-100 rounded-lg shadow-sm w-full max-w-lg mx-4',
          className,
        )}
      >
        {title && (
          <div className="flex items-center justify-between px-5 py-4 border-b border-ink-100">
            <h2 className="text-sm font-medium text-ink-800">{title}</h2>
            <button
              onClick={onClose}
              className="text-ink-400 hover:text-ink-600 transition-colors text-lg leading-none"
            >
              ×
            </button>
          </div>
        )}
        <div className="p-5">{children}</div>
      </div>
    </div>
  )
}
