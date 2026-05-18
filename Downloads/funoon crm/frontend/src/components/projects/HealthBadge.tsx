import { cn } from '../../lib/utils'

const config = {
  green: { label: 'Healthy', classes: 'bg-green-50 text-status-green' },
  amber: { label: 'Warning', classes: 'bg-amber-50 text-status-amber' },
  red:   { label: 'Critical', classes: 'bg-red-50 text-status-red' },
}

export function HealthBadge({ health }: { health: 'green' | 'amber' | 'red' }) {
  const { label, classes } = config[health] ?? config.green
  return (
    <span className={cn('inline-flex items-center text-xs px-2 py-0.5 rounded-full font-medium', classes)}>
      {label}
    </span>
  )
}
