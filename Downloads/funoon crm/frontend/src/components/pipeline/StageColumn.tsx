import type { Client } from '../../hooks/useClients'
import { stageLabelMap } from '../../lib/utils'
import { DealCard } from './DealCard'

interface StageColumnProps {
  stage: string
  clients: Client[]
}

export function StageColumn({ stage, clients }: StageColumnProps) {
  return (
    <div className="flex flex-col min-w-[220px] w-[220px]">
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-xs font-medium text-ink-500">{stageLabelMap(stage)}</span>
        <span className="text-xs text-ink-400">{clients.length}</span>
      </div>
      <div className="space-y-2 flex-1">
        {clients.map(c => (
          <DealCard key={c.id} client={c} />
        ))}
        {clients.length === 0 && (
          <div className="border border-dashed border-ink-100 rounded-lg h-16" />
        )}
      </div>
    </div>
  )
}
