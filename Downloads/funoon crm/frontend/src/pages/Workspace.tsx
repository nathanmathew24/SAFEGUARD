import { useEffect, useRef, useState } from 'react'
import { TopBar } from '../components/layout/TopBar'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { api } from '../lib/api'
import { formatRelative } from '../lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

type Tab = 'ask' | 'sops' | 'incidents'

export function Workspace() {
  const [tab, setTab] = useState<Tab>('ask')

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Workspace" />
      <div className="flex border-b border-ink-100 bg-white px-6">
        {(['ask', 'sops', 'incidents'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm transition-colors border-b-2 -mb-px capitalize
              ${tab === t ? 'border-ink-800 text-ink-800 font-medium' : 'border-transparent text-ink-400 hover:text-ink-600'}`}
          >
            {t === 'ask' ? 'Ask AI' : t === 'sops' ? 'SOPs' : 'Incidents'}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === 'ask' && <AskAI />}
        {tab === 'sops' && <SOPs />}
        {tab === 'incidents' && <Incidents />}
      </div>
    </div>
  )
}

// ── Ask AI ─────────────────────────────────────────────────────────────────────

function AskAI() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    if (!input.trim() || loading) return
    const userMsg: Message = { role: 'user', content: input, timestamp: new Date().toISOString() }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const res = await api.post<{ reply: string; conversation_id: string }>('/workspace/ask', {
        message: input,
        conversation_id: conversationId,
      })
      setConversationId(res.data.conversation_id)
      setMessages(m => [...m, { role: 'assistant', content: res.data.reply, timestamp: new Date().toISOString() }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: 'Error — could not reach backend.', timestamp: new Date().toISOString() }])
    } finally {
      setLoading(false)
    }
  }

  const SUGGESTIONS = [
    "What's the status of all live projects?",
    "Which invoices are overdue?",
    "What's the current MRR?",
    "List all open blockers across projects.",
  ]

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-6">
            <p className="text-sm text-ink-500">Ask anything about the CRM — clients, projects, finances, ops.</p>
            <div className="grid grid-cols-2 gap-2">
              {SUGGESTIONS.map(s => (
                <button
                  key={s}
                  onClick={() => { setInput(s); }}
                  className="text-left text-xs p-3 border border-ink-100 rounded-lg text-ink-600 hover:bg-ink-50 hover:border-ink-200 transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl rounded-lg px-4 py-3 text-sm ${
              m.role === 'user'
                ? 'bg-ink-900 text-white'
                : 'bg-white border border-ink-100 text-ink-800'
            }`}>
              <p className="whitespace-pre-wrap">{m.content}</p>
              <p className={`text-xs mt-1 ${m.role === 'user' ? 'text-ink-400' : 'text-ink-400'}`}>
                {formatRelative(m.timestamp)}
              </p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-ink-100 rounded-lg px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 bg-ink-300 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 150}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="p-4 border-t border-ink-100 bg-white">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about clients, projects, finances..."
            className="flex-1 text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400"
            disabled={loading}
          />
          <Button onClick={send} disabled={loading || !input.trim()}>Send</Button>
        </div>
        {conversationId && (
          <button
            onClick={() => { setMessages([]); setConversationId(null) }}
            className="text-xs text-ink-400 hover:text-ink-600 mt-2"
          >
            New conversation
          </button>
        )}
      </div>
    </div>
  )
}

// ── SOPs ──────────────────────────────────────────────────────────────────────

function SOPs() {
  const [sops, setSops] = useState<Array<{ id: string; title: string; category: string | null; content: string; updated_at: string }>>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ title: '', category: '', content: '' })

  useEffect(() => {
    api.get('/workspace/sops').then(r => setSops(r.data))
  }, [])

  const selectedSOP = sops.find(s => s.id === selected)

  async function handleCreate() {
    const res = await api.post('/workspace/sops', form)
    setSops(s => [...s, res.data])
    setShowNew(false)
    setForm({ title: '', category: '', content: '' })
  }

  return (
    <div className="flex h-full">
      <div className="w-64 border-r border-ink-100 p-4 space-y-2 overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-medium text-ink-400">SOPs</p>
          <button onClick={() => setShowNew(true)} className="text-xs text-ink-400 hover:text-ink-600">+ New</button>
        </div>
        {sops.map(s => (
          <button
            key={s.id}
            onClick={() => setSelected(s.id)}
            className={`w-full text-left px-2 py-1.5 rounded text-sm transition-colors
              ${selected === s.id ? 'bg-ink-100 text-ink-800 font-medium' : 'text-ink-600 hover:bg-ink-50'}`}
          >
            {s.title}
          </button>
        ))}
        {sops.length === 0 && <p className="text-xs text-ink-400">No SOPs yet.</p>}
      </div>
      <div className="flex-1 p-6 overflow-y-auto">
        {selectedSOP ? (
          <div>
            <h2 className="text-base font-medium text-ink-800 mb-1">{selectedSOP.title}</h2>
            {selectedSOP.category && <p className="text-xs text-ink-400 mb-4">{selectedSOP.category}</p>}
            <pre className="text-sm text-ink-700 whitespace-pre-wrap font-sans">{selectedSOP.content}</pre>
          </div>
        ) : (
          <p className="text-sm text-ink-400">Select an SOP to read it.</p>
        )}
      </div>
      {showNew && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-ink-900/40" onClick={() => setShowNew(false)} />
          <div className="relative bg-white border border-ink-100 rounded-lg shadow-sm w-full max-w-lg mx-4 p-5 space-y-3">
            <h2 className="text-sm font-medium">New SOP</h2>
            <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Title" className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md" />
            <input value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))} placeholder="Category" className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md" />
            <textarea value={form.content} onChange={e => setForm(f => ({ ...f, content: e.target.value }))} placeholder="Content (markdown)" rows={8} className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md resize-none" />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Save</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Incidents ─────────────────────────────────────────────────────────────────

function Incidents() {
  const [incidents, setIncidents] = useState<Array<{ id: string; severity: string; description: string; root_cause: string | null; resolution: string | null; occurred_at: string }>>([])
  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ severity: 'medium', description: '', root_cause: '', resolution: '' })

  useEffect(() => {
    api.get('/workspace/incidents').then(r => setIncidents(r.data))
  }, [])

  const SEVERITY_VARIANT: Record<string, 'red' | 'amber' | 'neutral'> = {
    critical: 'red', high: 'red', medium: 'amber', low: 'neutral',
  }

  async function handleCreate() {
    const res = await api.post('/workspace/incidents', form)
    setIncidents(i => [res.data, ...i])
    setShowNew(false)
    setForm({ severity: 'medium', description: '', root_cause: '', resolution: '' })
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-ink-400">Incident log</p>
        <Button size="sm" onClick={() => setShowNew(true)}>+ Log incident</Button>
      </div>
      <div className="space-y-3">
        {incidents.length === 0 && <p className="text-sm text-ink-400">No incidents logged.</p>}
        {incidents.map(inc => (
          <div key={inc.id} className="bg-white border border-ink-100 rounded-lg p-4 space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant={SEVERITY_VARIANT[inc.severity] ?? 'neutral'}>{inc.severity}</Badge>
              <span className="text-xs text-ink-400">{formatRelative(inc.occurred_at)}</span>
            </div>
            <p className="text-sm text-ink-800">{inc.description}</p>
            {inc.root_cause && <p className="text-xs text-ink-500">Root cause: {inc.root_cause}</p>}
            {inc.resolution && <p className="text-xs text-status-green">Resolution: {inc.resolution}</p>}
          </div>
        ))}
      </div>
      {showNew && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-ink-900/40" onClick={() => setShowNew(false)} />
          <div className="relative bg-white border border-ink-100 rounded-lg shadow-sm w-full max-w-lg mx-4 p-5 space-y-3">
            <h2 className="text-sm font-medium">Log incident</h2>
            <select value={form.severity} onChange={e => setForm(f => ({ ...f, severity: e.target.value }))} className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md">
              {['low', 'medium', 'high', 'critical'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="What happened?" rows={3} className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md resize-none" />
            <input value={form.root_cause} onChange={e => setForm(f => ({ ...f, root_cause: e.target.value }))} placeholder="Root cause" className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md" />
            <input value={form.resolution} onChange={e => setForm(f => ({ ...f, resolution: e.target.value }))} placeholder="Resolution" className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md" />
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
              <Button onClick={handleCreate}>Save</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

