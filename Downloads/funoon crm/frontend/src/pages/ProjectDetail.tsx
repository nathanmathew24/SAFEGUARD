import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { TopBar } from '../components/layout/TopBar'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { BlockerList } from '../components/projects/BlockerList'
import { HealthBadge } from '../components/projects/HealthBadge'
import {
  useProject, useUpdateProject, useAddBlocker,
  useResolveBlocker, useAddProjectNote,
  useProjectAISummarise, useProjectAIClientUpdate,
} from '../hooks/useProjects'
import { formatDate, formatRelative } from '../lib/utils'

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: project, isLoading } = useProject(id!)

  const updateProject = useUpdateProject(id!)
  const addBlocker = useAddBlocker(id!)
  const resolveBlocker = useResolveBlocker(id!)
  const addNote = useAddProjectNote(id!)
  const summarise = useProjectAISummarise(id!)
  const clientUpdate = useProjectAIClientUpdate(id!)

  const [noteText, setNoteText] = useState('')
  const [aiText, setAiText] = useState('')
  const [showBlocker, setShowBlocker] = useState(false)
  const [blockerForm, setBlockerForm] = useState({ body: '', owner: '', due_date: '' })

  if (isLoading) return <div className="p-6 text-sm text-ink-400">Loading...</div>
  if (!project) return <div className="p-6 text-sm text-ink-400">Project not found.</div>

  async function handleNote() {
    if (!noteText.trim()) return
    await addNote.mutateAsync(noteText)
    setNoteText('')
  }

  async function handleAddBlocker() {
    if (!blockerForm.body.trim()) return
    await addBlocker.mutateAsync({
      body: blockerForm.body,
      owner: blockerForm.owner || undefined,
      due_date: blockerForm.due_date || undefined,
    })
    setShowBlocker(false)
    setBlockerForm({ body: '', owner: '', due_date: '' })
  }

  async function handleSummarise() {
    const res = await summarise.mutateAsync()
    setAiText(res.summary)
  }

  async function handleClientUpdate() {
    const res = await clientUpdate.mutateAsync()
    setAiText(res.message)
  }

  const healthOptions: Array<'green' | 'amber' | 'red'> = ['green', 'amber', 'red']

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title={project.name}
        actions={
          <Button variant="secondary" size="sm" onClick={() => navigate('/projects')}>
            ← Projects
          </Button>
        }
      />

      <div className="flex-1 overflow-auto p-6 grid grid-cols-3 gap-6 items-start">

        {/* Left col */}
        <div className="col-span-2 space-y-4">

          {/* Header */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <HealthBadge health={project.health} />
              <div className="flex gap-1">
                {healthOptions.map(h => (
                  <button
                    key={h}
                    onClick={() => updateProject.mutate({ health: h })}
                    className={`text-xs px-2 py-0.5 rounded-full transition-colors capitalize
                      ${project.health === h ? 'bg-ink-800 text-white' : 'text-ink-400 hover:bg-ink-50'}`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              {project.live_since && <Field label="Live since" value={formatDate(project.live_since)} />}
              {project.renewal_date && <Field label="Renewal" value={formatDate(project.renewal_date)} />}
            </div>

            {project.stack_tags && project.stack_tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {project.stack_tags.map(tag => (
                  <span key={tag} className="text-xs px-1.5 py-0.5 bg-ink-50 text-ink-500 rounded">{tag}</span>
                ))}
              </div>
            )}

            {project.external_links && Object.keys(project.external_links).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {Object.entries(project.external_links).map(([label, url]) => (
                  <a
                    key={label}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-status-blue hover:underline"
                    onClick={e => e.stopPropagation()}
                  >
                    {label} ↗
                  </a>
                ))}
              </div>
            )}
          </Card>

          {/* Blockers */}
          <Card className="p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs font-medium text-ink-400">Blockers</p>
              <Button size="sm" variant="secondary" onClick={() => setShowBlocker(true)}>+ Add</Button>
            </div>
            <BlockerList
              blockers={project.blockers}
              onResolve={id => resolveBlocker.mutate(id)}
              resolving={resolveBlocker.isPending}
            />
          </Card>

          {/* Notes */}
          <Card className="p-4">
            <p className="text-xs font-medium text-ink-400 mb-3">Notes</p>
            <div className="space-y-2 mb-3 max-h-64 overflow-y-auto">
              {project.notes.length === 0 && <p className="text-xs text-ink-400">No notes yet.</p>}
              {[...project.notes].reverse().map(n => (
                <div key={n.id} className="text-sm text-ink-700 border-b border-ink-50 pb-2">
                  <p>{n.body}</p>
                  <p className="text-xs text-ink-400 mt-0.5">{formatRelative(n.created_at)}</p>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <textarea
                value={noteText}
                onChange={e => setNoteText(e.target.value)}
                placeholder="Add a note..."
                rows={2}
                className="flex-1 text-sm px-3 py-2 border border-ink-200 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-ink-400"
              />
              <Button onClick={handleNote} disabled={addNote.isPending || !noteText.trim()}>Add</Button>
            </div>
          </Card>
        </div>

        {/* Right col */}
        <div className="space-y-4">
          <Card className="p-4 space-y-2">
            <p className="text-xs font-medium text-ink-400 mb-1">AI</p>
            <Button variant="secondary" size="sm" className="w-full justify-start" onClick={handleSummarise} disabled={summarise.isPending}>
              {summarise.isPending ? 'Summarising...' : 'Summarise for new member'}
            </Button>
            <Button variant="secondary" size="sm" className="w-full justify-start" onClick={handleClientUpdate} disabled={clientUpdate.isPending}>
              {clientUpdate.isPending ? 'Drafting...' : 'Draft client update'}
            </Button>
            {aiText && (
              <div className="mt-2 p-3 bg-ink-50 rounded-md border border-ink-100">
                <p className="text-xs text-ink-400 mb-1">Output — copy to use</p>
                <p className="text-xs text-ink-700 whitespace-pre-wrap">{aiText}</p>
                <button
                  onClick={() => navigator.clipboard.writeText(aiText)}
                  className="text-xs text-ink-400 hover:text-ink-600 mt-2"
                >
                  Copy
                </button>
              </div>
            )}
          </Card>
        </div>
      </div>

      <Modal open={showBlocker} onClose={() => setShowBlocker(false)} title="Add blocker">
        <div className="space-y-3">
          <Input label="Blocker *" value={blockerForm.body} onChange={e => setBlockerForm(f => ({ ...f, body: e.target.value }))} placeholder="What's blocked?" />
          <Input label="Owner" value={blockerForm.owner} onChange={e => setBlockerForm(f => ({ ...f, owner: e.target.value }))} />
          <Input label="Due date" type="date" value={blockerForm.due_date} onChange={e => setBlockerForm(f => ({ ...f, due_date: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowBlocker(false)}>Cancel</Button>
            <Button onClick={handleAddBlocker} disabled={addBlocker.isPending}>Add blocker</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-ink-400">{label}</p>
      <p className="text-sm text-ink-700">{value}</p>
    </div>
  )
}
