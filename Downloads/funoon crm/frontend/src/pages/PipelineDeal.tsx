import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { TopBar } from '../components/layout/TopBar'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { StageBadge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import {
  useClient, useMoveStage, useAddNote,
  useAISummarise, useAIFollowup,
} from '../hooks/useClients'
import { formatAED, formatDate, formatRelative, stageLabelMap } from '../lib/utils'

const STAGES = [
  'inbound', 'qualifying', 'proposal_sent',
  'negotiating', 'closed_won', 'live', 'churned',
]

export function PipelineDeal() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: client, isLoading } = useClient(id!)

  const moveStage = useMoveStage(id!)
  const addNote = useAddNote(id!)
  const summarise = useAISummarise(id!)
  const followup = useAIFollowup(id!)

  const [noteText, setNoteText] = useState('')
  const [aiDraft, setAiDraft] = useState('')
  const [showStageModal, setShowStageModal] = useState(false)
  const [targetStage, setTargetStage] = useState('')

  if (isLoading) return <div className="p-6 text-sm text-ink-400">Loading...</div>
  if (!client) return <div className="p-6 text-sm text-ink-400">Deal not found.</div>

  async function handleNote() {
    if (!noteText.trim()) return
    await addNote.mutateAsync(noteText)
    setNoteText('')
  }

  async function handleStageMove() {
    if (!targetStage) return
    await moveStage.mutateAsync({ to_stage: targetStage })
    setShowStageModal(false)
  }

  async function handleFollowup() {
    const res = await followup.mutateAsync()
    setAiDraft(res.message)
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title={client.name}
        actions={
          <Button variant="secondary" size="sm" onClick={() => navigate('/pipeline')}>
            ← Pipeline
          </Button>
        }
      />

      <div className="flex-1 overflow-auto p-6 grid grid-cols-3 gap-6 items-start">

        {/* Left col — details */}
        <div className="col-span-2 space-y-4">

          {/* Header card */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <StageBadge stage={client.stage} />
              <Button size="sm" variant="secondary" onClick={() => setShowStageModal(true)}>
                Move stage
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {client.contact_name && <Field label="Contact" value={client.contact_name} />}
              {client.whatsapp && <Field label="WhatsApp" value={client.whatsapp} />}
              {client.email && <Field label="Email" value={client.email} />}
              {client.source && <Field label="Source" value={client.source} />}
              {client.estimated_mrr && <Field label="Est. MRR" value={formatAED(client.estimated_mrr)} />}
              {client.next_action_due && <Field label="Due" value={formatDate(client.next_action_due)} />}
            </div>
            {client.enquiry && (
              <div>
                <p className="text-xs text-ink-400 mb-1">Enquiry</p>
                <p className="text-sm text-ink-700">{client.enquiry}</p>
              </div>
            )}
            {client.next_action && (
              <div className="border-t border-ink-50 pt-3">
                <p className="text-xs text-ink-400 mb-1">Next action</p>
                <p className="text-sm text-ink-700">→ {client.next_action}</p>
              </div>
            )}
          </Card>

          {/* AI context */}
          {client.ai_context && (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-medium text-ink-400">AI summary</p>
                <span className="text-xs text-ink-300">
                  {client.ai_context_updated_at ? formatRelative(client.ai_context_updated_at) : ''}
                </span>
              </div>
              <p className="text-sm text-ink-700 whitespace-pre-wrap">{client.ai_context}</p>
            </Card>
          )}

          {/* Notes */}
          <Card className="p-4">
            <p className="text-xs font-medium text-ink-400 mb-3">Notes</p>
            <div className="space-y-2 mb-3 max-h-64 overflow-y-auto">
              {client.notes.length === 0 && (
                <p className="text-xs text-ink-400">No notes yet.</p>
              )}
              {[...client.notes].reverse().map(note => (
                <div key={note.id} className="text-sm text-ink-700 border-b border-ink-50 pb-2">
                  <p>{note.body}</p>
                  <p className="text-xs text-ink-400 mt-0.5">{formatRelative(note.created_at)}</p>
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
              <Button onClick={handleNote} disabled={addNote.isPending || !noteText.trim()}>
                Add
              </Button>
            </div>
          </Card>
        </div>

        {/* Right col — AI + timeline */}
        <div className="space-y-4">

          {/* AI actions */}
          <Card className="p-4 space-y-2">
            <p className="text-xs font-medium text-ink-400 mb-1">AI</p>
            <Button
              variant="secondary"
              size="sm"
              className="w-full justify-start"
              onClick={() => summarise.mutate()}
              disabled={summarise.isPending}
            >
              {summarise.isPending ? 'Summarising...' : 'Summarise notes'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              className="w-full justify-start"
              onClick={handleFollowup}
              disabled={followup.isPending}
            >
              {followup.isPending ? 'Drafting...' : 'Draft follow-up'}
            </Button>
            {aiDraft && (
              <div className="mt-2 p-3 bg-ink-50 rounded-md border border-ink-100">
                <p className="text-xs text-ink-400 mb-1">Draft — copy to send</p>
                <p className="text-xs text-ink-700 whitespace-pre-wrap">{aiDraft}</p>
                <button
                  onClick={() => navigator.clipboard.writeText(aiDraft)}
                  className="text-xs text-ink-400 hover:text-ink-600 mt-2"
                >
                  Copy
                </button>
              </div>
            )}
          </Card>

          {/* Stage history */}
          <Card className="p-4">
            <p className="text-xs font-medium text-ink-400 mb-3">Timeline</p>
            <div className="space-y-2">
              {[...client.stage_history].reverse().map(h => (
                <div key={h.id} className="text-xs">
                  <span className="text-ink-500">
                    {h.from_stage ? `${stageLabelMap(h.from_stage)} → ` : ''}
                    <span className="font-medium text-ink-700">{stageLabelMap(h.to_stage)}</span>
                  </span>
                  <p className="text-ink-400">{formatRelative(h.moved_at)}</p>
                  {h.note && <p className="text-ink-500 mt-0.5 italic">{h.note}</p>}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Stage move modal */}
      <Modal open={showStageModal} onClose={() => setShowStageModal(false)} title="Move stage">
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            {STAGES.filter(s => s !== client.stage).map(s => (
              <button
                key={s}
                onClick={() => setTargetStage(s)}
                className={`px-3 py-2 text-sm rounded-md border transition-colors text-left
                  ${targetStage === s
                    ? 'border-ink-800 bg-ink-900 text-white'
                    : 'border-ink-200 text-ink-600 hover:bg-ink-50'}`}
              >
                {stageLabelMap(s)}
              </button>
            ))}
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowStageModal(false)}>Cancel</Button>
            <Button onClick={handleStageMove} disabled={!targetStage || moveStage.isPending}>
              {moveStage.isPending ? 'Moving...' : 'Move'}
            </Button>
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
