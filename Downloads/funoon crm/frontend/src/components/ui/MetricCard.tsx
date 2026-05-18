import { cn } from '../../lib/utils'

interface MetricCardProps {
  label: string
  value: string | number
  sub?: string
  trend?: 'up' | 'down' | 'neutral'
  className?: string
}

export function MetricCard({ label, value, sub, className }: MetricCardProps) {
  return (
    <div className={cn('bg-white border border-ink-100 rounded-lg p-4', className)}>
      <p className="text-xs text-ink-400 mb-1">{label}</p>
      <p className="text-xl font-medium text-ink-900">{value}</p>
      {sub && <p className="text-xs text-ink-400 mt-0.5">{sub}</p>}
    </div>
  )
}
