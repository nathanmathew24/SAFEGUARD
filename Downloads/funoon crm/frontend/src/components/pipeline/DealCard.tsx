import { useNavigate } from 'react-router-dom'
import type { Client } from '../../hooks/useClients'
import { formatAED, formatRelative } from '../../lib/utils'
import { Badge } from '../ui/Badge'

interface DealCardProps {
  client: Client
}

export function DealCard({ client }: DealCardProps) {
  const navigate = useNavigate()

  return (
    <div
      onClick={() => navigate(`/pipeline/${client.id}`)}
      className="bg-white border border-ink-100 rounded-lg p-3 cursor-pointer hover:border-ink-200 transition-colors space-y-2"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-ink-800 leading-tight">{client.name}</p>
        {client.estimated_mrr && (
          <span className="text-xs text-ink-400 whitespace-nowrap">{formatAED(client.estimated_mrr)}</span>
        )}
      </div>

      {client.enquiry && (
        <p className="text-xs text-ink-500 line-clamp-2">{client.enquiry}</p>
      )}

      <div className="flex items-center justify-between">
        {client.source ? (
          <Badge variant="neutral">{client.source}</Badge>
        ) : <span />}
        <span className="text-xs text-ink-400">{formatRelative(client.updated_at)}</span>
      </div>

      {client.next_action && (
        <p className="text-xs text-ink-500 border-t border-ink-50 pt-2">
          → {client.next_action}
        </p>
      )}
    </div>
  )
}
