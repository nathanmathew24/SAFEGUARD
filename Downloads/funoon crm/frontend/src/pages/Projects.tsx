import { useState } from 'react'
import { TopBar } from '../components/layout/TopBar'
import { ProjectCard } from '../components/projects/ProjectCard'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { EmptyState } from '../components/ui/EmptyState'
import { useProjects, useCreateProject } from '../hooks/useProjects'

const HEALTH_FILTERS = ['all', 'red', 'amber', 'green'] as const
type HealthFilter = typeof HEALTH_FILTERS[number]

export function Projects() {
  const [healthFilter, setHealthFilter] = useState<HealthFilter>('all')
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ name: '', stack_tags: '', live_since: '', renewal_date: '' })

  const { data: projects = [], isLoading } = useProjects()
  const create = useCreateProject()

  const filtered = healthFilter === 'all' ? projects : projects.filter(p => p.health === healthFilter)
  const sorted = [...filtered].sort((a, b) => {
    const order = { red: 0, amber: 1, green: 2 }
    return order[a.health] - order[b.health]
  })

  async function handleCreate() {
    if (!form.name.trim()) return
    await create.mutateAsync({
      name: form.name,
      stack_tags: form.stack_tags ? form.stack_tags.split(',').map(s => s.trim()).filter(Boolean) : undefined,
      live_since: form.live_since || undefined,
      renewal_date: form.renewal_date || undefined,
    })
    setShowNew(false)
    setForm({ name: '', stack_tags: '', live_since: '', renewal_date: '' })
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Projects"
        actions={<Button size="sm" onClick={() => setShowNew(true)}>+ New project</Button>}
      />

      <div className="px-6 py-2 border-b border-ink-100 bg-white flex items-center gap-2">
        {HEALTH_FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setHealthFilter(f)}
            className={`text-xs px-2.5 py-1 rounded-md transition-colors capitalize
              ${healthFilter === f ? 'bg-ink-900 text-white' : 'text-ink-500 hover:bg-ink-50'}`}
          >
            {f === 'all' ? `All (${projects.length})` : f}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="text-sm text-ink-400">Loading...</div>
        ) : sorted.length === 0 ? (
          <EmptyState
            title="No projects yet"
            description="Add a live client deployment to start tracking ops health."
            action={<Button onClick={() => setShowNew(true)}>+ New project</Button>}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sorted.map(p => <ProjectCard key={p.id} project={p} />)}
          </div>
        )}
      </div>

      <Modal open={showNew} onClose={() => setShowNew(false)} title="New project">
        <div className="space-y-3">
          <Input label="Project name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Al Wathba — WhatsApp Bot" />
          <Input label="Stack tags (comma separated)" value={form.stack_tags} onChange={e => setForm(f => ({ ...f, stack_tags: e.target.value }))} placeholder="fastapi, claude, railway" />
          <Input label="Live since" type="date" value={form.live_since} onChange={e => setForm(f => ({ ...f, live_since: e.target.value }))} />
          <Input label="Renewal date" type="date" value={form.renewal_date} onChange={e => setForm(f => ({ ...f, renewal_date: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={create.isPending}>
              {create.isPending ? 'Creating...' : 'Create project'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
