import type { Blocker } from '../../hooks/useProjects'
import { formatDate } from '../../lib/utils'
import { Button } from '../ui/Button'

interface BlockerListProps {
  blockers: Blocker[]
  onResolve: (id: string) => void
  resolving?: boolean
}

export function BlockerList({ blockers, onResolve, resolving }: BlockerListProps) {
  const open = blockers.filter(b => !b.resolved)
  const resolved = blockers.filter(b => b.resolved)

  return (
    <div className="space-y-2">
      {open.length === 0 && <p className="text-xs text-ink-400">No open blockers.</p>}
      {open.map(b => (
        <div key={b.id} className="flex items-start justify-between gap-3 p-2.5 bg-red-50 border border-red-100 rounded-md">
          <div className="flex-1 min-w-0">
            <p className="text-sm text-ink-800">{b.body}</p>
            <p className="text-xs text-ink-400 mt-0.5">
              {b.owner && <span>{b.owner} · </span>}
              {b.due_date
                ? <span className={new Date(b.due_date) < new Date() ? 'text-status-red font-medium' : ''}>
                    Due {formatDate(b.due_date)}
                  </span>
                : 'No due date'}
            </p>
          </div>
          <Button size="sm" variant="secondary" onClick={() => onResolve(b.id)} disabled={resolving}>
            Resolve
          </Button>
        </div>
      ))}
      {resolved.length > 0 && (
        <details className="mt-2">
          <summary className="text-xs text-ink-400 cursor-pointer">
            {resolved.length} resolved
          </summary>
          <div className="mt-2 space-y-1">
            {resolved.map(b => (
              <div key={b.id} className="p-2 bg-ink-50 rounded text-xs text-ink-400 line-through">
                {b.body}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
