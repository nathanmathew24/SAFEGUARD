import type { Client } from '../../hooks/useClients'
import { StageColumn } from './StageColumn'

const STAGES = [
  'inbound', 'qualifying', 'proposal_sent',
  'negotiating', 'closed_won', 'live', 'churned',
]

interface KanbanBoardProps {
  clients: Client[]
}

export function KanbanBoard({ clients }: KanbanBoardProps) {
  const byStage = (stage: string) => clients.filter(c => c.stage === stage)

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {STAGES.map(stage => (
        <StageColumn key={stage} stage={stage} clients={byStage(stage)} />
      ))}
    </div>
  )
}
