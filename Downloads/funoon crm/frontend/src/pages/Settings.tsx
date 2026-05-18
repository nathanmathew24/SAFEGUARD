import { useEffect, useState } from 'react'
import { TopBar } from '../components/layout/TopBar'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { api } from '../lib/api'

interface CompanySettings {
  id: string
  letterhead_path: string | null
  signature_path: string | null
  stamp_path: string | null
  company_name: string
  tagline: string | null
  address_line1: string | null
  address_line2: string | null
  trn: string | null
  email: string | null
  phone: string | null
  website: string | null
  bank_name: string | null
  bank_account_name: string | null
  bank_iban: string | null
  bank_account_number: string | null
  bank_swift: string | null
  bank_currency: string
  invoice_payment_terms: string | null
  invoice_notes: string | null
  invoice_prefix: string
  vat_rate: string
}

const empty: Omit<CompanySettings, 'id' | 'letterhead_path' | 'signature_path' | 'stamp_path'> = {
  company_name: '', tagline: '', address_line1: '', address_line2: '',
  trn: '', email: '', phone: '', website: '',
  bank_name: '', bank_account_name: '', bank_iban: '',
  bank_account_number: '', bank_swift: '', bank_currency: 'AED',
  invoice_payment_terms: '', invoice_notes: '',
  invoice_prefix: 'INV', vat_rate: '5',
}

type Section = 'company' | 'bank' | 'invoice' | 'assets' | 'telegram'

export function Settings() {
  const [settings, setSettings] = useState<Omit<CompanySettings, 'id' | 'letterhead_path' | 'signature_path' | 'stamp_path'>>(empty)
  const [tgToken, setTgToken] = useState('')
  const [tgChatId, setTgChatId] = useState('')
  const [tgSaving, setTgSaving] = useState(false)
  const [tgTesting, setTgTesting] = useState(false)
  const [tgStatus, setTgStatus] = useState('')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [letterheadPath, setLetterheadPath] = useState<string | null>(null)
  const [letterheadUploading, setLetterheadUploading] = useState(false)
  const [signaturePath, setSignaturePath] = useState<string | null>(null)
  const [stampPath, setStampPath] = useState<string | null>(null)
  const [signatureUploading, setSignatureUploading] = useState(false)
  const [stampUploading, setStampUploading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [section, setSection] = useState<Section>('company')

  useEffect(() => {
    api.get('/settings').then(r => {
      const s = r.data
      setLetterheadPath(s.letterhead_path ?? null)
      setSignaturePath(s.signature_path ?? null)
      setStampPath(s.stamp_path ?? null)
      setSettings({
        company_name:          s.company_name ?? '',
        tagline:               s.tagline ?? '',
        address_line1:         s.address_line1 ?? '',
        address_line2:         s.address_line2 ?? '',
        trn:                   s.trn ?? '',
        email:                 s.email ?? '',
        phone:                 s.phone ?? '',
        website:               s.website ?? '',
        bank_name:             s.bank_name ?? '',
        bank_account_name:     s.bank_account_name ?? '',
        bank_iban:             s.bank_iban ?? '',
        bank_account_number:   s.bank_account_number ?? '',
        bank_swift:            s.bank_swift ?? '',
        bank_currency:         s.bank_currency ?? 'AED',
        invoice_payment_terms: s.invoice_payment_terms ?? '',
        invoice_notes:         s.invoice_notes ?? '',
        invoice_prefix:        s.invoice_prefix ?? 'INV',
        vat_rate:              s.vat_rate ?? '5',
      })
      setLoading(false)
    })
  }, [])

  function set(field: keyof typeof settings, value: string) {
    setSettings(s => ({ ...s, [field]: value }))
    setSaved(false)
  }

  async function saveTelegram() {
    if (!tgToken || !tgChatId) { setTgStatus('Token and chat ID are required'); return }
    setTgSaving(true)
    setTgStatus('')
    try {
      // Save token + chat ID to .env
      await api.post(`/telegram/configure?token=${encodeURIComponent(tgToken)}&chat_id=${encodeURIComponent(tgChatId)}`)
      // Register webhook if URL provided
      if (webhookUrl) {
        const wr = await api.post(`/telegram/set-webhook?webhook_url=${encodeURIComponent(webhookUrl)}`)
        setTgStatus(wr.data.ok ? `✓ Saved. Webhook: ${wr.data.webhook_url}` : '✓ Saved. Webhook registration failed.')
      } else {
        setTgStatus('✓ Token and chat ID saved. Add webhook URL to go live.')
      }
    } catch (e: any) {
      setTgStatus(e?.response?.data?.detail || 'Error saving')
    }
    setTgSaving(false)
  }

  async function testTelegram() {
    setTgTesting(true)
    setTgStatus('')
    try {
      const res = await api.post('/telegram/send-test')
      setTgStatus(res.data.ok ? 'Test message sent to your chat!' : 'Failed')
    } catch (e: any) {
      setTgStatus(e?.response?.data?.detail || 'Error — check token and chat ID')
    }
    setTgTesting(false)
  }

  async function uploadAsset(
    type: 'signature' | 'stamp',
    file: File,
    setUploading: (v: boolean) => void,
    setPath: (v: string | null) => void,
  ) {
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    const res = await api.post(`/settings/${type}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    setPath(res.data[`${type}_path`])
    setUploading(false)
  }

  async function removeAsset(
    type: 'signature' | 'stamp',
    setPath: (v: string | null) => void,
  ) {
    await api.delete(`/settings/${type}`)
    setPath(null)
  }

  async function uploadLetterhead(file: File) {
    setLetterheadUploading(true)
    const form = new FormData()
    form.append('file', file)
    const res = await api.post('/settings/letterhead', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    setLetterheadPath(res.data.letterhead_path)
    setLetterheadUploading(false)
  }

  async function removeLetterhead() {
    await api.delete('/settings/letterhead')
    setLetterheadPath(null)
  }

  async function save() {
    setSaving(true)
    await api.patch('/settings', settings)
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  if (loading) return <div className="p-6 text-sm text-ink-400">Loading...</div>

  const SECTIONS: { id: Section; label: string }[] = [
    { id: 'company', label: 'Company' },
    { id: 'bank',    label: 'Bank & payment' },
    { id: 'invoice', label: 'Invoice defaults' },
    { id: 'assets',   label: 'Signature & stamp' },
    { id: 'telegram', label: 'Telegram bot' },
  ]

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Settings"
        actions={
          <Button size="sm" onClick={save} disabled={saving}>
            {saving ? 'Saving...' : saved ? 'Saved' : 'Save changes'}
          </Button>
        }
      />

      <div className="flex flex-1 overflow-hidden">
        {/* Left nav */}
        <div className="w-48 border-r border-ink-100 p-4 space-y-1 shrink-0">
          {SECTIONS.map(s => (
            <button
              key={s.id}
              onClick={() => setSection(s.id)}
              className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors
                ${section === s.id ? 'bg-ink-100 text-ink-800 font-medium' : 'text-ink-500 hover:bg-ink-50'}`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-8">
          {section === 'company' && (
            <Section title="Company profile" description="Appears on invoices and client communications.">

              {/* Letterhead upload */}
              <div className="p-4 border border-ink-100 rounded-lg bg-ink-50 space-y-3">
                <div>
                  <p className="text-xs font-medium text-ink-700">Invoice letterhead</p>
                  <p className="text-xs text-ink-400 mt-0.5">
                    Upload a PNG or JPG of your letterhead. It will replace the text header on all invoice PDFs.
                  </p>
                </div>

                {letterheadPath ? (
                  <div className="space-y-2">
                    <div className="border border-ink-200 rounded-md overflow-hidden bg-white">
                      <img
                        src="/api/settings/letterhead/file"
                        alt="Letterhead preview"
                        className="w-full object-contain max-h-32"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-status-green">Letterhead uploaded</span>
                      <label className="text-xs text-status-blue hover:underline cursor-pointer">
                        Replace
                        <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden"
                          onChange={e => { if (e.target.files?.[0]) uploadLetterhead(e.target.files[0]) }} />
                      </label>
                      <button onClick={removeLetterhead} className="text-xs text-status-red hover:underline">Remove</button>
                    </div>
                  </div>
                ) : (
                  <label className={`flex flex-col items-center justify-center border-2 border-dashed border-ink-200 rounded-lg p-6 cursor-pointer hover:border-ink-400 transition-colors ${letterheadUploading ? 'opacity-50' : ''}`}>
                    <span className="text-sm text-ink-400">{letterheadUploading ? 'Uploading...' : 'Click to upload letterhead'}</span>
                    <span className="text-xs text-ink-300 mt-1">PNG, JPG, WebP · max ~2MB</span>
                    <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" disabled={letterheadUploading}
                      onChange={e => { if (e.target.files?.[0]) uploadLetterhead(e.target.files[0]) }} />
                  </label>
                )}
              </div>

              <Row>
                <Input label="Company name" value={settings.company_name} onChange={e => set('company_name', e.target.value)} placeholder="Funoon FZC" />
                <Input label="Tagline" value={settings.tagline ?? ''} onChange={e => set('tagline', e.target.value)} placeholder="AI automation for UAE businesses" />
              </Row>
              <Row>
                <Input label="Address line 1" value={settings.address_line1 ?? ''} onChange={e => set('address_line1', e.target.value)} placeholder="Dubai, United Arab Emirates" />
                <Input label="Address line 2" value={settings.address_line2 ?? ''} onChange={e => set('address_line2', e.target.value)} placeholder="Free Zone, Suite 00" />
              </Row>
              <Row>
                <Input label="Email" value={settings.email ?? ''} onChange={e => set('email', e.target.value)} placeholder="farzeelfaz@gmail.com" />
                <Input label="Phone / WhatsApp" value={settings.phone ?? ''} onChange={e => set('phone', e.target.value)} placeholder="+971 50 756 2833" />
              </Row>
              <Row>
                <Input label="Website" value={settings.website ?? ''} onChange={e => set('website', e.target.value)} placeholder="funoon.ai" />
                <Input label="TRN (UAE Tax Registration)" value={settings.trn ?? ''} onChange={e => set('trn', e.target.value)} placeholder="100xxxxxxxxx003" />
              </Row>
            </Section>
          )}

          {section === 'bank' && (
            <Section title="Bank & payment details" description="These appear in the Payment Details section of every invoice PDF.">
              <Row>
                <Input label="Bank name" value={settings.bank_name ?? ''} onChange={e => set('bank_name', e.target.value)} placeholder="Emirates NBD" />
                <Input label="Account name" value={settings.bank_account_name ?? ''} onChange={e => set('bank_account_name', e.target.value)} placeholder="Funoon FZC" />
              </Row>
              <Row>
                <Input label="IBAN" value={settings.bank_iban ?? ''} onChange={e => set('bank_iban', e.target.value)} placeholder="AE00 0000 0000 0000 0000 000" />
                <Input label="Account number" value={settings.bank_account_number ?? ''} onChange={e => set('bank_account_number', e.target.value)} placeholder="1234567890" />
              </Row>
              <Row>
                <Input label="SWIFT / BIC" value={settings.bank_swift ?? ''} onChange={e => set('bank_swift', e.target.value)} placeholder="EBILAEAD" />
                <Input label="Currency" value={settings.bank_currency} onChange={e => set('bank_currency', e.target.value)} placeholder="AED" />
              </Row>
            </Section>
          )}

          {section === 'telegram' && (
            <Section title="Telegram bot" description="Connect a Telegram bot so you can create invoices, log deals and check status by sending a message.">
              <div className="space-y-4 max-w-lg">

                {/* Setup guide */}
                <div className="p-4 bg-ink-50 border border-ink-100 rounded-lg text-xs text-ink-600 space-y-1.5">
                  <p className="font-medium text-ink-800">Setup (one time)</p>
                  <p>1. Open Telegram → search <span className="font-mono bg-ink-100 px-1 rounded">@BotFather</span></p>
                  <p>2. Send <span className="font-mono bg-ink-100 px-1 rounded">/newbot</span> → follow prompts → copy the token</p>
                  <p>3. Paste token below and save</p>
                  <p>4. Send <span className="font-mono bg-ink-100 px-1 rounded">/start</span> to your new bot, then click "Get my chat ID" below</p>
                  <p>5. Paste your webhook URL (e.g. <span className="font-mono bg-ink-100 px-1 rounded">https://yourapp.railway.app</span>) and click Register</p>
                </div>

                <Input
                  label="Bot token (from @BotFather)"
                  value={tgToken}
                  onChange={e => setTgToken(e.target.value)}
                  placeholder="7123456789:AAFxxx..."
                />

                <div>
                  <label className="block text-xs text-ink-500 mb-1">Your chat ID</label>
                  <div className="flex gap-2">
                    <input
                      value={tgChatId}
                      onChange={e => setTgChatId(e.target.value)}
                      placeholder="e.g. 123456789"
                      className="flex-1 text-sm px-3 py-2 border border-ink-200 rounded-md focus:outline-none focus:ring-1 focus:ring-ink-400"
                    />
                    <a
                      href="https://t.me/userinfobot"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs px-3 py-2 border border-ink-200 rounded-md text-ink-500 hover:bg-ink-50 whitespace-nowrap"
                    >
                      Get my ID ↗
                    </a>
                  </div>
                  <p className="text-xs text-ink-400 mt-1">Only messages from this chat ID will be processed.</p>
                </div>

                <Input
                  label="Webhook base URL (your deployed app URL)"
                  value={webhookUrl}
                  onChange={e => setWebhookUrl(e.target.value)}
                  placeholder="https://yourapp.railway.app"
                />

                <div className="flex gap-2 pt-1">
                  <Button onClick={saveTelegram} disabled={tgSaving}>
                    {tgSaving ? 'Saving...' : 'Save & register webhook'}
                  </Button>
                  <Button variant="secondary" onClick={testTelegram} disabled={tgTesting}>
                    {tgTesting ? 'Sending...' : 'Send test message'}
                  </Button>
                </div>

                {tgStatus && (
                  <p className={`text-xs ${tgStatus.includes('Error') || tgStatus.includes('fail') ? 'text-status-red' : 'text-status-green'}`}>
                    {tgStatus}
                  </p>
                )}

                {/* What you can say */}
                <div className="p-4 border border-ink-100 rounded-lg space-y-2">
                  <p className="text-xs font-medium text-ink-700">What you can say</p>
                  {[
                    ['Create invoice',  '"invoice Al Wathba 1500 for WhatsApp bot retainer"'],
                    ['New deal',        '"new deal Kandy Cars, enquiry chatbot, est 2000/month"'],
                    ['Add note',        '"note on Al Wathba: client confirmed renewal"'],
                    ['Check status',    '"what\'s the status of Al Wathba?"'],
                    ['Overdue',         '"show overdue invoices"'],
                  ].map(([label, example]) => (
                    <div key={label} className="flex gap-3">
                      <span className="text-xs text-ink-400 w-28 shrink-0">{label}</span>
                      <span className="text-xs font-mono text-ink-600">{example}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Section>
          )}

          {section === 'assets' && (
            <Section title="Signature & stamp" description="Uploaded images appear on all invoice PDFs in the signature and stamp boxes.">
              <div className="grid grid-cols-2 gap-6">

                {/* Signature */}
                <div className="space-y-3">
                  <p className="text-xs font-medium text-ink-700">Authorised signature</p>
                  <p className="text-xs text-ink-400">PNG or JPG with transparent background recommended.</p>
                  {signaturePath ? (
                    <div className="space-y-2">
                      <div className="border border-ink-200 rounded-md bg-white p-3 flex items-center justify-center h-24">
                        <img src="/api/settings/signature/file" alt="Signature" className="max-h-20 max-w-full object-contain" />
                      </div>
                      <div className="flex gap-3">
                        <label className="text-xs text-status-blue hover:underline cursor-pointer">
                          Replace
                          <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden"
                            onChange={e => { if (e.target.files?.[0]) uploadAsset('signature', e.target.files[0], setSignatureUploading, setSignaturePath) }} />
                        </label>
                        <button onClick={() => removeAsset('signature', setSignaturePath)} className="text-xs text-status-red hover:underline">Remove</button>
                      </div>
                    </div>
                  ) : (
                    <label className={`flex flex-col items-center justify-center border-2 border-dashed border-ink-200 rounded-lg p-6 cursor-pointer hover:border-ink-400 transition-colors ${signatureUploading ? 'opacity-50' : ''}`}>
                      <span className="text-sm text-ink-400">{signatureUploading ? 'Uploading...' : 'Click to upload signature'}</span>
                      <span className="text-xs text-ink-300 mt-1">PNG with transparent bg · max 2MB</span>
                      <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" disabled={signatureUploading}
                        onChange={e => { if (e.target.files?.[0]) uploadAsset('signature', e.target.files[0], setSignatureUploading, setSignaturePath) }} />
                    </label>
                  )}
                </div>

                {/* Stamp */}
                <div className="space-y-3">
                  <p className="text-xs font-medium text-ink-700">Company stamp</p>
                  <p className="text-xs text-ink-400">PNG with transparent background works best for stamps.</p>
                  {stampPath ? (
                    <div className="space-y-2">
                      <div className="border border-ink-200 rounded-md bg-white p-3 flex items-center justify-center h-24">
                        <img src="/api/settings/stamp/file" alt="Stamp" className="max-h-20 max-w-full object-contain" />
                      </div>
                      <div className="flex gap-3">
                        <label className="text-xs text-status-blue hover:underline cursor-pointer">
                          Replace
                          <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden"
                            onChange={e => { if (e.target.files?.[0]) uploadAsset('stamp', e.target.files[0], setStampUploading, setStampPath) }} />
                        </label>
                        <button onClick={() => removeAsset('stamp', setStampPath)} className="text-xs text-status-red hover:underline">Remove</button>
                      </div>
                    </div>
                  ) : (
                    <label className={`flex flex-col items-center justify-center border-2 border-dashed border-ink-200 rounded-lg p-6 cursor-pointer hover:border-ink-400 transition-colors ${stampUploading ? 'opacity-50' : ''}`}>
                      <span className="text-sm text-ink-400">{stampUploading ? 'Uploading...' : 'Click to upload stamp'}</span>
                      <span className="text-xs text-ink-300 mt-1">PNG with transparent bg · max 2MB</span>
                      <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" disabled={stampUploading}
                        onChange={e => { if (e.target.files?.[0]) uploadAsset('stamp', e.target.files[0], setStampUploading, setStampPath) }} />
                    </label>
                  )}
                </div>
              </div>

              {/* Preview */}
              <div className="mt-4 p-4 border border-ink-100 rounded-lg bg-ink-50">
                <p className="text-xs font-medium text-ink-400 mb-3">How it appears on invoices</p>
                <div className="flex gap-6">
                  <div className="flex-1 border-b border-ink-300 pb-1">
                    {signaturePath
                      ? <img src="/api/settings/signature/file" alt="sig" className="h-10 object-contain mb-1" />
                      : <div className="h-10" />}
                    <p className="text-xs text-ink-400 tracking-wider">AUTHORISED SIGNATURE</p>
                  </div>
                  <div className="w-24" />
                  <div className="flex-1 border-b border-ink-300 pb-1">
                    {stampPath
                      ? <img src="/api/settings/stamp/file" alt="stamp" className="h-10 object-contain mb-1" />
                      : <div className="h-10" />}
                    <p className="text-xs text-ink-400 tracking-wider">COMPANY STAMP</p>
                  </div>
                </div>
              </div>
            </Section>
          )}

          {section === 'invoice' && (
            <Section title="Invoice defaults" description="Pre-filled on every new invoice.">
              <Row>
                <Input label="Invoice prefix" value={settings.invoice_prefix} onChange={e => set('invoice_prefix', e.target.value)} placeholder="INV" />
                <Input label="VAT rate (%)" type="number" value={settings.vat_rate} onChange={e => set('vat_rate', e.target.value)} placeholder="5" />
              </Row>
              <div>
                <label className="block text-xs text-ink-500 mb-1">Payment terms</label>
                <textarea
                  value={settings.invoice_payment_terms ?? ''}
                  onChange={e => set('invoice_payment_terms', e.target.value)}
                  rows={2}
                  placeholder="Payment due within 30 days of issue."
                  className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-ink-400"
                />
              </div>
              <div>
                <label className="block text-xs text-ink-500 mb-1">Default invoice note</label>
                <textarea
                  value={settings.invoice_notes ?? ''}
                  onChange={e => set('invoice_notes', e.target.value)}
                  rows={2}
                  placeholder="Thank you for your business."
                  className="w-full text-sm px-3 py-2 border border-ink-200 rounded-md resize-none focus:outline-none focus:ring-1 focus:ring-ink-400"
                />
              </div>

              {/* Preview */}
              <div className="mt-6 p-4 border border-ink-100 rounded-lg bg-ink-50">
                <p className="text-xs font-medium text-ink-400 mb-3">Invoice header preview</p>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-base font-medium text-ink-900">{settings.company_name || 'Company name'}</p>
                    <p className="text-xs text-ink-500 mt-1">{settings.address_line1 || 'Address'}</p>
                    {settings.address_line2 && <p className="text-xs text-ink-500">{settings.address_line2}</p>}
                    {settings.trn && <p className="text-xs text-ink-500">TRN: {settings.trn}</p>}
                    <p className="text-xs text-ink-500">{settings.email}</p>
                    <p className="text-xs text-ink-500">{settings.website}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-ink-400">INVOICE</p>
                    <p className="text-xs text-ink-600 mt-1">{settings.invoice_prefix}-001</p>
                    <p className="text-xs text-ink-500">VAT {settings.vat_rate}%</p>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-ink-200">
                  <p className="text-xs font-medium text-ink-400 mb-1">Payment details preview</p>
                  <p className="text-xs text-ink-600">Bank: {settings.bank_name}</p>
                  <p className="text-xs text-ink-600">Account: {settings.bank_account_name}</p>
                  <p className="text-xs text-ink-600">IBAN: {settings.bank_iban}</p>
                  {settings.bank_swift && <p className="text-xs text-ink-600">SWIFT: {settings.bank_swift}</p>}
                </div>
              </div>
            </Section>
          )}
        </div>
      </div>
    </div>
  )
}

function Section({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <div className="max-w-2xl space-y-4">
      <div className="mb-6">
        <h2 className="text-sm font-medium text-ink-800">{title}</h2>
        <p className="text-xs text-ink-400 mt-1">{description}</p>
      </div>
      {children}
    </div>
  )
}

function Row({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-2 gap-4">{children}</div>
}
