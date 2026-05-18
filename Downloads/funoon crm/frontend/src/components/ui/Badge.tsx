import { cn } from '../../lib/utils'

type BadgeVariant = 'green' | 'amber' | 'red' | 'blue' | 'neutral'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

const variantClasses: Record<BadgeVariant, string> = {
  green:   'bg-green-50 text-status-green',
  amber:   'bg-amber-50 text-status-amber',
  red:     'bg-red-50 text-status-red',
  blue:    'bg-blue-50 text-status-blue',
  neutral: 'bg-ink-100 text-ink-500',
}

export function Badge({ variant = 'neutral', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center text-xs px-2 py-0.5 rounded-full font-medium',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function HealthBadge({ health }: { health: 'green' | 'amber' | 'red' }) {
  const labels = { green: 'Healthy', amber: 'Warning', red: 'Critical' }
  return <Badge variant={health}>{labels[health]}</Badge>
}

export function StageBadge({ stage }: { stage: string }) {
  const stageVariants: Record<string, BadgeVariant> = {
    inbound:       'neutral',
    qualifying:    'blue',
    proposal_sent: 'blue',
    negotiating:   'amber',
    closed_won:    'green',
    live:          'green',
    churned:       'red',
  }
  return <Badge variant={stageVariants[stage] ?? 'neutral'}>{stage.replace('_', ' ')}</Badge>
}
