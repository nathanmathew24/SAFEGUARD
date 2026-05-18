import { useState } from 'react'
import { TopBar } from '../components/layout/TopBar'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { useComponents, useCreateComponent, useAISuggestComponents } from '../hooks/useLibrary'

const STATUS_VARIANT: Record<string, 'green' | 'amber' | 'red' | 'neutral'> = {
  stable: 'green', 'in-development': 'amber', deprecated: 'red',
}

const CATEGORIES = ['messaging', 'voice', 'lead-scoring', 'scheduling', 'sheets-integration', 'ai-persona', 'other']

export function Library() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [showAI, setShowAI] = useState(false)
  const [aiQuery, setAiQuery] = useState('')
  const [aiResult, setAiResult] = useState('')
  const [form, setForm] = useState({ name: '', category: '', description: '', tech_tags: '', version: '', github_path: '' })

  const { data: components = [], isLoading } = useComponents({ q: search || undefined, category: category || undefined })
  const create = useCreateComponent()
  const aiSuggest = useAISuggestComponents()

  async function handleCreate() {
    if (!form.name || !form.category) return
    await create.mutateAsync({
      name: form.name,
      category: form.category,
      description: form.description || undefined,
      tech_tags: form.tech_tags ? form.tech_tags.split(',').map(s => s.trim()).filter(Boolean) : undefined,
      version: form.version || undefined,
      github_path: form.github_path || undefined,
    })
    setShowNew(false)
    setForm({ name: '', category: '', description: '', tech_tags: '', version: '', github_path: '' })
  }

  async function handleAISuggest() {
    if (!aiQuery.trim()) return
    const res = await aiSuggest.mutateAsync(aiQuery)
    setAiResult(res.suggestion)
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Library"
        actions={
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" onClick={() => setShowAI(true)}>Ask AI</Button>
            <Button size="sm" onClick={() => setShowNew(true)}>+ Component</Button>
          </div>
        }
      />

      {/* Filters */}
      <div className="px-6 py-3 border-b border-ink-100 bg-white flex items-center gap-3">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search..."
          className="text-sm px-3 py-1.5 border border-ink-200 rounded-md w-48 focus:outline-none focus:ring-1 focus:ring-ink-400"
        />
        <div className="flex gap-1">
          <button
            onClick={() => setCategory('')}
            className={`text-xs px-2 py-1 rounded transition-colors ${!category ? 'bg-ink-900 text-white' : 'text-ink-500 hover:bg-ink-50'}`}
          >
            All
          </button>
          {CATEGORIES.map(c => (
            <button
              key={c}
              onClick={() => setCategory(c === category ? '' : c)}
              className={`text-xs px-2 py-1 rounded transition-colors ${category === c ? 'bg-ink-900 text-white' : 'text-ink-500 hover:bg-ink-50'}`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="text-sm text-ink-400">Loading...</div>
        ) : components.length === 0 ? (
          <EmptyState
            title="No components yet"
            description="Catalogue your reusable automation components here."
            action={<Button onClick={() => setShowNew(true)}>+ Component</Button>}
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {components.map(c => (
              <Card key={c.id} className="p-4 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium text-ink-800">{c.name}</p>
                  <Badge variant={STATUS_VARIANT[c.status] ?? 'neutral'}>{c.status}</Badge>
                </div>
                <p className="text-xs text-ink-400 capitalize">{c.category}</p>
                {c.description && <p className="text-xs text-ink-600">{c.description}</p>}
                {c.tech_tags && c.tech_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {c.tech_tags.map(tag => (
                      <span key={tag} className="text-xs px-1.5 py-0.5 bg-ink-50 text-ink-500 rounded">{tag}</span>
                    ))}
                  </div>
                )}
                <div className="flex items-center justify-between text-xs text-ink-400">
                  {c.version && <span>v{c.version}</span>}
                  {c.github_path && (
                    <a href={c.github_path} target="_blank" rel="noopener noreferrer" className="text-status-blue hover:underline">
                      GitHub ↗
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* New component */}
      <Modal open={showNew} onClose={() => setShowNew(false)} title="New component">
        <div className="space-y-3">
          <Input label="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          <div>
            <label className="block text-xs text-ink-500 mb-1">Category *</label>
            <select
              value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
              className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400"
            >
              <option value="">Select...</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <Input label="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          <Input label="Tech tags (comma separated)" value={form.tech_tags} onChange={e => setForm(f => ({ ...f, tech_tags: e.target.value }))} placeholder="fastapi, claude, redis" />
          <Input label="Version" value={form.version} onChange={e => setForm(f => ({ ...f, version: e.target.value }))} placeholder="1.0.0" />
          <Input label="GitHub path" value={form.github_path} onChange={e => setForm(f => ({ ...f, github_path: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={create.isPending}>Add component</Button>
          </div>
        </div>
      </Modal>

      {/* AI suggest */}
      <Modal open={showAI} onClose={() => { setShowAI(false); setAiResult('') }} title="What components do I need?">
        <div className="space-y-3">
          <textarea
            value={aiQuery}
            onChange={e => setAiQuery(e.target.value)}
            placeholder="Describe the project you want to build..."
            rows={3}
            className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-ink-400"
          />
          <Button onClick={handleAISuggest} disabled={aiSuggest.isPending || !aiQuery.trim()} className="w-full">
            {aiSuggest.isPending ? 'Thinking...' : 'Ask'}
          </Button>
          {aiResult && (
            <div className="p-3 bg-ink-50 rounded-md border border-ink-100">
              <p className="text-xs text-ink-700 whitespace-pre-wrap">{aiResult}</p>
            </div>
          )}
        </div>
      </Modal>
    </div>
  )
}
