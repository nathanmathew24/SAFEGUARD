import { cn } from '../../lib/utils'

interface CardProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export function Card({ children, className, onClick }: CardProps) {
  return (
    <div
      className={cn(
        'bg-white border border-ink-100 rounded-lg',
        onClick && 'cursor-pointer hover:border-ink-200 transition-colors',
        className,
      )}
      onClick={onClick}
    >
      {children}
    </div>
  )
}
