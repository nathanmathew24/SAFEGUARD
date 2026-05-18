import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { KanbanBoard } from '../components/pipeline/KanbanBoard'
import { TopBar } from '../components/layout/TopBar'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { Modal } from '../components/ui/Modal'
import { Input } from '../components/ui/Input'
import { StageBadge } from '../components/ui/Badge'
import { useClients, useCreateClient } from '../hooks/useClients'
import { formatAED, formatRelative } from '../lib/utils'

type View = 'kanban' | 'table'

export function Pipeline() {
  const navigate = useNavigate()
  const [view, setView] = useState<View>('kanban')
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ name: '', contact_name: '', whatsapp: '', enquiry: '', estimated_mrr: '' })

  const { data: clients = [], isLoading } = useClients()
  const create = useCreateClient()

  async function handleCreate() {
    if (!form.name.trim()) return
    await create.mutateAsync({
      name: form.name,
      contact_name: form.contact_name || undefined,
      whatsapp: form.whatsapp || undefined,
      enquiry: form.enquiry || undefined,
      estimated_mrr: form.estimated_mrr ? parseInt(form.estimated_mrr) : undefined,
    })
    setShowNew(false)
    setForm({ name: '', contact_name: '', whatsapp: '', enquiry: '', estimated_mrr: '' })
  }

  const totalMRR = clients
    .filter(c => c.stage === 'live')
    .reduce((sum, c) => sum + (c.estimated_mrr ?? 0), 0)

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Pipeline"
        actions={
          <div className="flex items-center gap-2">
            <div className="flex border border-ink-200 rounded-md overflow-hidden">
              <button
                onClick={() => setView('kanban')}
                className={`px-2.5 py-1 text-xs transition-colors ${view === 'kanban' ? 'bg-ink-900 text-white' : 'text-ink-500 hover:bg-ink-50'}`}
              >
                Board
              </button>
              <button
                onClick={() => setView('table')}
                className={`px-2.5 py-1 text-xs transition-colors ${view === 'table' ? 'bg-ink-900 text-white' : 'text-ink-500 hover:bg-ink-50'}`}
              >
                Table
              </button>
            </div>
            <Button size="sm" onClick={() => setShowNew(true)}>+ New deal</Button>
          </div>
        }
      />

      {/* Summary bar */}
      <div className="px-6 py-2 border-b border-ink-100 flex items-center gap-6 bg-white">
        <span className="text-xs text-ink-500">{clients.length} deals</span>
        <span className="text-xs text-ink-500">Live MRR: <span className="text-ink-800 font-medium">{formatAED(totalMRR)}</span></span>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="text-sm text-ink-400">Loading...</div>
        ) : clients.length === 0 ? (
          <EmptyState
            title="No deals yet"
            description="Add your first prospect to start tracking the pipeline."
            action={<Button onClick={() => setShowNew(true)}>+ New deal</Button>}
          />
        ) : view === 'kanban' ? (
          <KanbanBoard clients={clients} />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-100 text-left">
                <th className="pb-2 text-xs font-medium text-ink-400 pr-4">Company</th>
                <th className="pb-2 text-xs font-medium text-ink-400 pr-4">Stage</th>
                <th className="pb-2 text-xs font-medium text-ink-400 pr-4">MRR</th>
                <th className="pb-2 text-xs font-medium text-ink-400 pr-4">Source</th>
                <th className="pb-2 text-xs font-medium text-ink-400 pr-4">Next action</th>
                <th className="pb-2 text-xs font-medium text-ink-400">Updated</th>
              </tr>
            </thead>
            <tbody>
              {clients.map(c => (
                <tr
                  key={c.id}
                  onClick={() => navigate(`/pipeline/${c.id}`)}
                  className="border-b border-ink-50 hover:bg-ink-50 cursor-pointer transition-colors"
                >
                  <td className="py-2.5 pr-4">
                    <span className="font-medium text-ink-800">{c.name}</span>
                    {c.contact_name && <span className="text-ink-400 ml-2">{c.contact_name}</span>}
                  </td>
                  <td className="py-2.5 pr-4"><StageBadge stage={c.stage} /></td>
                  <td className="py-2.5 pr-4 text-ink-600">{c.estimated_mrr ? formatAED(c.estimated_mrr) : '—'}</td>
                  <td className="py-2.5 pr-4 text-ink-500">{c.source ?? '—'}</td>
                  <td className="py-2.5 pr-4 text-ink-500 max-w-[200px] truncate">{c.next_action ?? '—'}</td>
                  <td className="py-2.5 text-ink-400">{formatRelative(c.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Modal open={showNew} onClose={() => setShowNew(false)} title="New deal">
        <div className="space-y-3">
          <Input label="Company name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Al Wathba Auto" />
          <Input label="Contact name" value={form.contact_name} onChange={e => setForm(f => ({ ...f, contact_name: e.target.value }))} />
          <Input label="WhatsApp" value={form.whatsapp} onChange={e => setForm(f => ({ ...f, whatsapp: e.target.value }))} placeholder="+971..." />
          <Input label="Enquiry" value={form.enquiry} onChange={e => setForm(f => ({ ...f, enquiry: e.target.value }))} placeholder="What automation they need" />
          <Input label="Est. MRR (AED)" type="number" value={form.estimated_mrr} onChange={e => setForm(f => ({ ...f, estimated_mrr: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={create.isPending}>
              {create.isPending ? 'Creating...' : 'Create deal'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
