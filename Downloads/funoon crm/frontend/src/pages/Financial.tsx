import { useState } from 'react'
import { TopBar } from '../components/layout/TopBar'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { MetricCard } from '../components/ui/MetricCard'
import { Modal } from '../components/ui/Modal'
import { EmptyState } from '../components/ui/EmptyState'
import {
  useBillingRecords, useCreateBilling, useUpdateBilling, useDeleteBilling,
  useCreateExpense, useDeleteExpense, useExpenses,
  useCreateInfraCost, useDeleteInfraCost, useInfraCosts,
  useCreateInvoice, useDeleteInvoice, useInvoices, useUpdateInvoice,
  useFinancialSummary, usePLSummary, useProjectMargins,
  type LineItem,
} from '../hooks/useFinancial'
import { useClients } from '../hooks/useClients'
import { formatAED, formatDate } from '../lib/utils'

type Tab = 'overview' | 'invoices' | 'billing' | 'costs' | 'pl'

const STATUS_VARIANT: Record<string, 'green' | 'amber' | 'red' | 'neutral'> = {
  paid: 'green', draft: 'neutral', sent: 'amber', overdue: 'red',
  active: 'green', paused: 'amber', churned: 'red',
}

export function Financial() {
  const [tab, setTab] = useState<Tab>('overview')

  return (
    <div className="flex flex-col h-full">
      <TopBar title="Financial" />
      <div className="flex border-b border-ink-100 bg-white px-6">
        {(['overview', 'invoices', 'billing', 'costs', 'pl'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm transition-colors border-b-2 -mb-px capitalize
              ${tab === t ? 'border-ink-800 text-ink-800 font-medium' : 'border-transparent text-ink-400 hover:text-ink-600'}`}
          >
            {t === 'pl' ? 'P&L' : t}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === 'overview' && <OverviewTab />}
        {tab === 'invoices' && <InvoicesTab />}
        {tab === 'billing' && <BillingTab />}
        {tab === 'costs' && <CostsTab />}
        {tab === 'pl' && <PLTab />}
      </div>
    </div>
  )
}

// ── Overview ──────────────────────────────────────────────────────────────────

function OverviewTab() {
  const { data: summary } = useFinancialSummary()
  const { data: margins = [] } = useProjectMargins()
  const { data: invoices = [] } = useInvoices()

  const overdue = invoices.filter(i => i.status === 'overdue')

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      {summary && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="MRR" value={formatAED(summary.mrr)} sub="monthly recurring" />
            <MetricCard label="ARR" value={formatAED(summary.arr)} />
            <MetricCard label="Net margin (month)" value={formatAED(summary.net_margin_month)}
              sub={`Revenue − costs`} />
            <MetricCard label="Revenue at risk" value={formatAED(summary.revenue_at_risk)}
              sub="churned + paused" />
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard label="Total costs (month)" value={formatAED(summary.total_cost_month)}
              sub={`Infra + expenses`} />
            <MetricCard label="Infra (month)" value={formatAED(summary.infra_cost_month)} />
            <MetricCard label="Expenses (month)" value={formatAED(summary.expense_total_month)} />
            <MetricCard label="Collected (month)" value={formatAED(summary.revenue_collected_month)}
              sub="paid invoices" />
          </div>
        </>
      )}

      {overdue.length > 0 && (
        <div className="bg-red-50 border border-red-100 rounded-lg p-4">
          <p className="text-xs font-medium text-status-red mb-2">{overdue.length} overdue invoice{overdue.length > 1 ? 's' : ''}</p>
          <div className="space-y-1">
            {overdue.map(inv => (
              <p key={inv.id} className="text-sm text-ink-700">
                {inv.client_name || '—'} · {inv.number || inv.id.slice(0, 8)} · {formatAED(inv.amount)}
                {inv.due_date && <span className="text-xs text-ink-400 ml-2">due {formatDate(inv.due_date)}</span>}
              </p>
            ))}
          </div>
        </div>
      )}

      {margins.length > 0 && (
        <div>
          <h2 className="text-xs font-medium text-ink-400 mb-3">Per-project margin</h2>
          <div className="border border-ink-100 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50">
                <tr>
                  <th className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">Project</th>
                  <th className="text-right px-4 py-2.5 text-xs font-medium text-ink-400">MRR</th>
                  <th className="text-right px-4 py-2.5 text-xs font-medium text-ink-400">Infra</th>
                  <th className="text-right px-4 py-2.5 text-xs font-medium text-ink-400">Margin</th>
                  <th className="text-right px-4 py-2.5 text-xs font-medium text-ink-400">%</th>
                </tr>
              </thead>
              <tbody>
                {margins.map(m => (
                  <tr key={m.project_id} className="border-t border-ink-100">
                    <td className="px-4 py-3 text-ink-800">{m.project_name}</td>
                    <td className="px-4 py-3 text-right text-ink-600">{formatAED(m.mrr)}</td>
                    <td className="px-4 py-3 text-right text-ink-600">{formatAED(m.infra_cost)}</td>
                    <td className={`px-4 py-3 text-right font-medium ${m.margin >= 0 ? 'text-status-green' : 'text-status-red'}`}>
                      {formatAED(m.margin)}
                    </td>
                    <td className={`px-4 py-3 text-right text-xs ${m.margin_pct >= 0 ? 'text-status-green' : 'text-status-red'}`}>
                      {m.margin_pct}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Invoices ──────────────────────────────────────────────────────────────────

function InvoicesTab() {
  const { data: invoices = [] } = useInvoices()
  const { data: clients = [] } = useClients()
  const createInvoice = useCreateInvoice()
  const updateInvoice = useUpdateInvoice()
  const deleteInvoice = useDeleteInvoice()

  const [showNew, setShowNew] = useState(false)
  const [filter, setFilter] = useState<string>('all')
  const [form, setForm] = useState({ number: '', client_id: '', due_date: '', issued_date: '', notes: '', doc_type: 'invoice' })
  const [lineItems, setLineItems] = useState<LineItem[]>([{ description: '', qty: 1, unit_price: 0 }])

  const subtotal = lineItems.reduce((s, i) => s + i.qty * i.unit_price, 0)
  const vat = Math.round(subtotal * 0.05)
  const total = subtotal + vat

  const filtered = filter === 'all' ? invoices : invoices.filter(i => i.status === filter)

  async function handleCreate() {
    if (!lineItems[0]?.description) return
    await createInvoice.mutateAsync({
      number: form.number || undefined,
      client_id: form.client_id || undefined,
      amount: total,
      issued_date: form.issued_date || new Date().toISOString().split('T')[0],
      due_date: form.due_date || undefined,
      notes: form.notes || undefined,
      status: 'draft',
      doc_type: form.doc_type,
      line_items: lineItems.filter(l => l.description),
    })
    setShowNew(false)
    setForm({ number: '', client_id: '', due_date: '', issued_date: '', notes: '', doc_type: 'invoice' })
    setLineItems([{ description: '', qty: 1, unit_price: 0 }])
  }

  const STATUS_FLOW: Record<string, string> = { draft: 'sent', sent: 'paid' }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-3 border-b border-ink-100 bg-white flex items-center justify-between">
        <div className="flex gap-1">
          {['all', 'draft', 'sent', 'paid', 'overdue'].map(s => (
            <button key={s} onClick={() => setFilter(s)}
              className={`text-xs px-2.5 py-1 rounded-md capitalize transition-colors
                ${filter === s ? 'bg-ink-900 text-white' : 'text-ink-500 hover:bg-ink-50'}`}>
              {s}
            </button>
          ))}
        </div>
        <Button size="sm" onClick={() => setShowNew(true)}>+ Invoice</Button>
      </div>

      <div className="flex-1 overflow-auto p-6">
        {filtered.length === 0 ? (
          <EmptyState title="No invoices" action={<Button onClick={() => setShowNew(true)}>+ Invoice</Button>} />
        ) : (
          <div className="border border-ink-100 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50">
                <tr>
                  {['Invoice #', 'Client', 'Amount', 'Issued', 'Due', 'Status', ''].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map(inv => (
                  <tr key={inv.id} className={`border-t border-ink-100 hover:bg-ink-50 transition-colors
                    ${inv.status === 'overdue' ? 'bg-red-50 hover:bg-red-50' : ''}`}>
                    <td className="px-4 py-3 font-medium text-ink-800">{inv.number || '—'}</td>
                    <td className="px-4 py-3 text-ink-600">{inv.client_name || '—'}</td>
                    <td className="px-4 py-3 font-medium">{formatAED(inv.amount)}</td>
                    <td className="px-4 py-3 text-ink-500">{inv.issued_date ? formatDate(inv.issued_date) : '—'}</td>
                    <td className="px-4 py-3 text-ink-500">{inv.due_date ? formatDate(inv.due_date) : '—'}</td>
                    <td className="px-4 py-3">
                      <Badge variant={STATUS_VARIANT[inv.status] ?? 'neutral'}>{inv.status}</Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <button onClick={() => window.open(`/api/financial/invoices/${inv.id}/pdf`, '_blank')}
                          className="text-xs text-status-blue hover:underline">PDF</button>
                        {STATUS_FLOW[inv.status] && (
                          <button
                            onClick={() => updateInvoice.mutate({ id: inv.id, data: { status: STATUS_FLOW[inv.status] } })}
                            className="text-xs text-ink-400 hover:text-ink-700 transition-colors">
                            Mark {STATUS_FLOW[inv.status]}
                          </button>
                        )}
                        {inv.status === 'draft' && (
                          <button onClick={() => deleteInvoice.mutate(inv.id)}
                            className="text-xs text-ink-300 hover:text-status-red transition-colors">Delete</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={showNew} onClose={() => setShowNew(false)} title="New invoice" className="max-w-2xl">
        <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-ink-500 mb-1">Document type</label>
              <select value={form.doc_type} onChange={e => setForm(f => ({ ...f, doc_type: e.target.value }))}
                className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400">
                <option value="invoice">Invoice</option>
                <option value="receipt">Receipt</option>
                <option value="quote">Quote</option>
              </select>
            </div>
            <Input label="Number" value={form.number} onChange={e => setForm(f => ({ ...f, number: e.target.value }))} placeholder="INV-001" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-ink-500 mb-1">Client</label>
              <select value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))}
                className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400">
                <option value="">Select client...</option>
                {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <Input label="Issue date" type="date" value={form.issued_date} onChange={e => setForm(f => ({ ...f, issued_date: e.target.value }))} />
            <Input label="Due date" type="date" value={form.due_date} onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} />
          </div>
          <Input label="Notes" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />

          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-medium text-ink-500">Line items</p>
              <button onClick={() => setLineItems(l => [...l, { description: '', qty: 1, unit_price: 0 }])}
                className="text-xs text-ink-400 hover:text-ink-600">+ Add line</button>
            </div>
            <div className="space-y-2">
              <div className="grid grid-cols-[1fr_60px_100px_80px_20px] gap-2 text-xs text-ink-400 px-1">
                <span>Description</span><span className="text-center">Qty</span>
                <span className="text-right">Unit price</span><span className="text-right">Amount</span><span />
              </div>
              {lineItems.map((item, idx) => (
                <div key={idx} className="grid grid-cols-[1fr_60px_100px_80px_20px] gap-2 items-center">
                  <input value={item.description} onChange={e => setLineItems(l => l.map((x, i) => i === idx ? { ...x, description: e.target.value } : x))}
                    placeholder="e.g. WhatsApp bot — monthly retainer"
                    className="text-sm px-3 py-1.5 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400" />
                  <input type="number" value={item.qty} onChange={e => setLineItems(l => l.map((x, i) => i === idx ? { ...x, qty: parseInt(e.target.value) || 1 } : x))}
                    className="text-sm px-2 py-1.5 border border-ink-200 rounded-md text-center focus:outline-none" />
                  <input type="number" value={item.unit_price} onChange={e => setLineItems(l => l.map((x, i) => i === idx ? { ...x, unit_price: parseInt(e.target.value) || 0 } : x))}
                    className="text-sm px-2 py-1.5 border border-ink-200 rounded-md text-right focus:outline-none" />
                  <span className="text-xs text-ink-500 text-right">{formatAED(item.qty * item.unit_price)}</span>
                  {lineItems.length > 1 && (
                    <button onClick={() => setLineItems(l => l.filter((_, i) => i !== idx))}
                      className="text-ink-300 hover:text-status-red text-base leading-none">×</button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="border-t border-ink-100 pt-3 space-y-1 text-sm">
            <div className="flex justify-between text-ink-500"><span>Subtotal</span><span>{formatAED(subtotal)}</span></div>
            <div className="flex justify-between text-ink-500"><span>VAT (5%)</span><span>{formatAED(vat)}</span></div>
            <div className="flex justify-between font-medium text-ink-900 text-base pt-1 border-t border-ink-100">
              <span>Total</span><span>{formatAED(total)}</span>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={createInvoice.isPending}>
              {createInvoice.isPending ? 'Creating...' : 'Create invoice'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// ── Billing records ────────────────────────────────────────────────────────────

function BillingTab() {
  const { data: billing = [] } = useBillingRecords()
  const { data: clients = [] } = useClients()
  const createBilling = useCreateBilling()
  const updateBilling = useUpdateBilling()
  const deleteBilling = useDeleteBilling()

  const [showNew, setShowNew] = useState(false)
  const [form, setForm] = useState({ client_id: '', amount: '', cycle: 'monthly', started_at: '', notes: '' })

  const mrr = billing.filter(b => b.status === 'active' && b.cycle === 'monthly').reduce((s, b) => s + b.amount, 0)

  async function handleCreate() {
    if (!form.client_id || !form.amount) return
    await createBilling.mutateAsync({
      client_id: form.client_id,
      amount: parseInt(form.amount),
      cycle: form.cycle,
      status: 'active',
      started_at: form.started_at || undefined,
      notes: form.notes || undefined,
    })
    setShowNew(false)
    setForm({ client_id: '', amount: '', cycle: 'monthly', started_at: '', notes: '' })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-3 border-b border-ink-100 bg-white flex items-center justify-between">
        <span className="text-xs text-ink-500">MRR from active monthly: <span className="font-medium text-ink-800">{formatAED(mrr)}</span></span>
        <Button size="sm" onClick={() => setShowNew(true)}>+ Billing record</Button>
      </div>
      <div className="flex-1 overflow-auto p-6">
        {billing.length === 0 ? (
          <EmptyState title="No billing records" description="Add a billing record per client to track MRR." action={<Button onClick={() => setShowNew(true)}>+ Add</Button>} />
        ) : (
          <div className="border border-ink-100 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50">
                <tr>
                  {['Client', 'Amount', 'Cycle', 'Status', 'Started', 'Notes', ''].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {billing.map(b => (
                  <tr key={b.id} className="border-t border-ink-100 hover:bg-ink-50 transition-colors">
                    <td className="px-4 py-3 font-medium text-ink-800">{b.client_name || b.client_id.slice(0, 8)}</td>
                    <td className="px-4 py-3 font-medium">{formatAED(b.amount)}</td>
                    <td className="px-4 py-3 text-ink-600 capitalize">{b.cycle}</td>
                    <td className="px-4 py-3"><Badge variant={STATUS_VARIANT[b.status] ?? 'neutral'}>{b.status}</Badge></td>
                    <td className="px-4 py-3 text-ink-500">{b.started_at ? formatDate(b.started_at) : '—'}</td>
                    <td className="px-4 py-3 text-ink-500 max-w-[160px] truncate">{b.notes || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {b.status === 'active' && (
                          <button onClick={() => updateBilling.mutate({ id: b.id, data: { status: 'paused' } })}
                            className="text-xs text-ink-400 hover:text-status-amber transition-colors">Pause</button>
                        )}
                        {b.status === 'paused' && (
                          <button onClick={() => updateBilling.mutate({ id: b.id, data: { status: 'active' } })}
                            className="text-xs text-ink-400 hover:text-status-green transition-colors">Resume</button>
                        )}
                        {b.status !== 'churned' && (
                          <button onClick={() => updateBilling.mutate({ id: b.id, data: { status: 'churned', ended_at: new Date().toISOString().split('T')[0] } })}
                            className="text-xs text-ink-400 hover:text-status-red transition-colors">Churn</button>
                        )}
                        <button onClick={() => deleteBilling.mutate(b.id)}
                          className="text-xs text-ink-300 hover:text-status-red transition-colors">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={showNew} onClose={() => setShowNew(false)} title="New billing record">
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-ink-500 mb-1">Client *</label>
            <select value={form.client_id} onChange={e => setForm(f => ({ ...f, client_id: e.target.value }))}
              className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400">
              <option value="">Select client...</option>
              {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <Input label="Amount (AED) *" type="number" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} placeholder="1500" />
          <div>
            <label className="block text-xs text-ink-500 mb-1">Cycle</label>
            <select value={form.cycle} onChange={e => setForm(f => ({ ...f, cycle: e.target.value }))}
              className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400">
              {['monthly', 'quarterly', 'annually', 'one-time'].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <Input label="Started" type="date" value={form.started_at} onChange={e => setForm(f => ({ ...f, started_at: e.target.value }))} />
          <Input label="Notes" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowNew(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={createBilling.isPending}>Add record</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// ── Costs (infra + expenses) ───────────────────────────────────────────────────

function CostsTab() {
  const today = new Date()
  const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-01`

  const { data: infra = [] } = useInfraCosts()
  const { data: expenses = [] } = useExpenses()
  const createInfra = useCreateInfraCost()
  const deleteInfra = useDeleteInfraCost()
  const createExpense = useCreateExpense()
  const deleteExpense = useDeleteExpense()

  const [showInfra, setShowInfra] = useState(false)
  const [showExpense, setShowExpense] = useState(false)
  const [infraForm, setInfraForm] = useState({ service: '', amount: '', month: currentMonth, notes: '' })
  const [expForm, setExpForm] = useState({ category: 'tool', description: '', amount: '', month: currentMonth, recurring: false, notes: '' })

  const totalInfra = infra.reduce((s, c) => s + c.amount, 0)
  const totalExp = expenses.reduce((s, e) => s + e.amount, 0)

  const EXPENSE_CATEGORIES = ['salary', 'tool', 'subscription', 'travel', 'marketing', 'other']
  const INFRA_SERVICES = ['railway', 'anthropic', 'twilio', 'elevenlabs', 'vercel', 'aws', 'other']

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      {/* Infra costs */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-xs font-medium text-ink-400">Infrastructure costs</h2>
            <p className="text-sm font-medium text-ink-800 mt-0.5">{formatAED(totalInfra)} total logged</p>
          </div>
          <Button size="sm" variant="secondary" onClick={() => setShowInfra(true)}>+ Add cost</Button>
        </div>
        {infra.length === 0 ? (
          <p className="text-xs text-ink-400">No infra costs logged yet.</p>
        ) : (
          <div className="border border-ink-100 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50">
                <tr>
                  {['Service', 'Amount', 'Month', 'Notes', ''].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {infra.map(c => (
                  <tr key={c.id} className="border-t border-ink-100 hover:bg-ink-50">
                    <td className="px-4 py-3 capitalize font-medium text-ink-700">{c.service}</td>
                    <td className="px-4 py-3">{formatAED(c.amount)}</td>
                    <td className="px-4 py-3 text-ink-500">{c.month.slice(0, 7)}</td>
                    <td className="px-4 py-3 text-ink-500">{c.notes || '—'}</td>
                    <td className="px-4 py-3">
                      <button onClick={() => deleteInfra.mutate(c.id)} className="text-xs text-ink-300 hover:text-status-red">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Expenses */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-xs font-medium text-ink-400">Operating expenses</h2>
            <p className="text-sm font-medium text-ink-800 mt-0.5">{formatAED(totalExp)} total logged</p>
          </div>
          <Button size="sm" variant="secondary" onClick={() => setShowExpense(true)}>+ Add expense</Button>
        </div>
        {expenses.length === 0 ? (
          <p className="text-xs text-ink-400">No expenses logged yet.</p>
        ) : (
          <div className="border border-ink-100 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-ink-50">
                <tr>
                  {['Category', 'Description', 'Amount', 'Month', 'Recurring', ''].map(h => (
                    <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {expenses.map(e => (
                  <tr key={e.id} className="border-t border-ink-100 hover:bg-ink-50">
                    <td className="px-4 py-3 capitalize text-ink-600">{e.category}</td>
                    <td className="px-4 py-3 text-ink-800">{e.description}</td>
                    <td className="px-4 py-3 font-medium">{formatAED(e.amount)}</td>
                    <td className="px-4 py-3 text-ink-500">{e.month.slice(0, 7)}</td>
                    <td className="px-4 py-3">{e.recurring ? <Badge variant="blue">Yes</Badge> : <span className="text-ink-400 text-xs">No</span>}</td>
                    <td className="px-4 py-3">
                      <button onClick={() => deleteExpense.mutate(e.id)} className="text-xs text-ink-300 hover:text-status-red">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Infra modal */}
      <Modal open={showInfra} onClose={() => setShowInfra(false)} title="Add infra cost">
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-ink-500 mb-1">Service</label>
            <select value={infraForm.service} onChange={e => setInfraForm(f => ({ ...f, service: e.target.value }))}
              className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400">
              <option value="">Select...</option>
              {INFRA_SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <Input label="Amount (AED)" type="number" value={infraForm.amount} onChange={e => setInfraForm(f => ({ ...f, amount: e.target.value }))} />
          <Input label="Month" type="date" value={infraForm.month} onChange={e => setInfraForm(f => ({ ...f, month: e.target.value }))} />
          <Input label="Notes" value={infraForm.notes} onChange={e => setInfraForm(f => ({ ...f, notes: e.target.value }))} />
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowInfra(false)}>Cancel</Button>
            <Button onClick={async () => {
              if (!infraForm.service || !infraForm.amount) return
              await createInfra.mutateAsync({ service: infraForm.service, amount: parseInt(infraForm.amount), month: infraForm.month, notes: infraForm.notes || undefined })
              setShowInfra(false)
              setInfraForm({ service: '', amount: '', month: currentMonth, notes: '' })
            }}>Add</Button>
          </div>
        </div>
      </Modal>

      {/* Expense modal */}
      <Modal open={showExpense} onClose={() => setShowExpense(false)} title="Add expense">
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-ink-500 mb-1">Category</label>
            <select value={expForm.category} onChange={e => setExpForm(f => ({ ...f, category: e.target.value }))}
              className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400">
              {EXPENSE_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <Input label="Description" value={expForm.description} onChange={e => setExpForm(f => ({ ...f, description: e.target.value }))} placeholder="e.g. Notion subscription" />
          <Input label="Amount (AED)" type="number" value={expForm.amount} onChange={e => setExpForm(f => ({ ...f, amount: e.target.value }))} />
          <Input label="Month" type="date" value={expForm.month} onChange={e => setExpForm(f => ({ ...f, month: e.target.value }))} />
          <label className="flex items-center gap-2 text-sm text-ink-600 cursor-pointer">
            <input type="checkbox" checked={expForm.recurring} onChange={e => setExpForm(f => ({ ...f, recurring: e.target.checked }))} className="rounded" />
            Recurring monthly
          </label>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="secondary" onClick={() => setShowExpense(false)}>Cancel</Button>
            <Button onClick={async () => {
              if (!expForm.description || !expForm.amount) return
              await createExpense.mutateAsync({ category: expForm.category, description: expForm.description, amount: parseInt(expForm.amount), month: expForm.month, recurring: expForm.recurring, notes: undefined })
              setShowExpense(false)
              setExpForm({ category: 'tool', description: '', amount: '', month: currentMonth, recurring: false, notes: '' })
            }}>Add</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// ── P&L ───────────────────────────────────────────────────────────────────────

function PLTab() {
  const { data: pl } = usePLSummary(6)
  const rows = pl?.rows ?? []
  const maxRevenue = Math.max(...rows.map(r => r.revenue), 1)

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <h2 className="text-xs font-medium text-ink-400">Profit & Loss — last 6 months</h2>

      {/* Bar chart (CSS-only) */}
      {rows.length > 0 && (
        <div className="flex items-end gap-3 h-32 bg-ink-50 rounded-lg p-4">
          {rows.map(r => (
            <div key={r.month} className="flex-1 flex flex-col items-center gap-1">
              <div className="w-full flex flex-col justify-end" style={{ height: '80px' }}>
                <div
                  className={`w-full rounded-sm transition-all ${r.net >= 0 ? 'bg-status-green' : 'bg-status-red'}`}
                  style={{ height: `${Math.max(4, Math.abs(r.revenue) / maxRevenue * 80)}px` }}
                  title={`Revenue: ${formatAED(r.revenue)}`}
                />
              </div>
              <span className="text-xs text-ink-400">{r.month.slice(5, 7)}/{r.month.slice(2, 4)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="border border-ink-100 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-ink-50">
            <tr>
              {['Month', 'Revenue', 'Infra', 'Expenses', 'Total cost', 'Net'].map(h => (
                <th key={h} className="text-left px-4 py-2.5 text-xs font-medium text-ink-400">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.month} className="border-t border-ink-100 hover:bg-ink-50">
                <td className="px-4 py-3 font-medium text-ink-700">{r.month}</td>
                <td className="px-4 py-3 text-status-green">{formatAED(r.revenue)}</td>
                <td className="px-4 py-3 text-ink-600">{formatAED(r.infra_cost)}</td>
                <td className="px-4 py-3 text-ink-600">{formatAED(r.expenses)}</td>
                <td className="px-4 py-3 text-ink-600">{formatAED(r.total_cost)}</td>
                <td className={`px-4 py-3 font-medium ${r.net >= 0 ? 'text-status-green' : 'text-status-red'}`}>
                  {r.net >= 0 ? '+' : ''}{formatAED(r.net)}
                </td>
              </tr>
            ))}
            {rows.length > 0 && (() => {
              const totals = rows.reduce((acc, r) => ({
                revenue: acc.revenue + r.revenue,
                total_cost: acc.total_cost + r.total_cost,
                net: acc.net + r.net,
              }), { revenue: 0, total_cost: 0, net: 0 })
              return (
                <tr className="border-t-2 border-ink-200 bg-ink-50 font-medium">
                  <td className="px-4 py-3 text-ink-600">Total</td>
                  <td className="px-4 py-3 text-status-green">{formatAED(totals.revenue)}</td>
                  <td className="px-4 py-3 text-ink-600" />
                  <td className="px-4 py-3 text-ink-600" />
                  <td className="px-4 py-3 text-ink-600">{formatAED(totals.total_cost)}</td>
                  <td className={`px-4 py-3 ${totals.net >= 0 ? 'text-status-green' : 'text-status-red'}`}>
                    {totals.net >= 0 ? '+' : ''}{formatAED(totals.net)}
                  </td>
                </tr>
              )
            })()}
          </tbody>
        </table>
      </div>
    </div>
  )
}
