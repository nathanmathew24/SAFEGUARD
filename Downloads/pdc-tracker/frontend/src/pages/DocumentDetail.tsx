import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, Ban, CheckCircle } from 'lucide-react';
import api, { formatAED, formatDate } from '../lib/api';
import { useLang } from '../contexts/LangContext';
import { useAuth } from '../contexts/AuthContext';

export default function DocumentDetail() {
  const { docType = 'invoices', id } = useParams<{ docType: string; id: string }>();
  const { t } = useLang();
  const { isOwner, isFinance } = useAuth();
  const navigate = useNavigate();

  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [voidReason, setVoidReason] = useState('');
  const [tab, setTab] = useState<'detail' | 'audit'>('detail');
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    api.get(`/${docType}/${id}`)
      .then((r) => setDoc(r.data.data))
      .catch(() => navigate(-1))
      .finally(() => setLoading(false));
    api.get(`/audit-log?table_name=${docType}&record_id=${id}`)
      .then((r) => setAuditLog(r.data.data ?? [])).catch(() => {});
  }, [docType, id]);

  const generatePDF = async () => {
    try {
      // strip trailing 's' to get model slug (invoices → invoice)
      const slug = docType.replace(/-/g, '_').replace(/s$/, '');
      const r = await api.post(`/${slug}/${id}/generate-pdf`);
      const token = r.data.data.download_token;
      window.open(`/api/pdf/download/${token}`, '_blank');
    } catch {
      setError(t('PDF generation failed.', 'فشل إنشاء PDF.'));
    }
  };

  const voidDoc = async () => {
    if (!voidReason.trim()) { setError(t('Void reason is required.', 'سبب الإلغاء مطلوب.')); return; }
    try {
      await api.post(`/${docType}/${id}/void`, { reason: voidReason });
      setDoc((d: any) => ({ ...d, is_voided: true, status: 'voided', void_reason: voidReason }));
      setVoidReason('');
    } catch (e: any) {
      setError(e.response?.data?.message ?? t('Failed to void.', 'فشل الإلغاء.'));
    }
  };

  const confirmDoc = async () => {
    try {
      await api.post(`/${docType}/${id}/confirm`);
      setDoc((d: any) => ({ ...d, status: 'confirmed' }));
    } catch (e: any) {
      setError(e.response?.data?.message ?? t('Failed to confirm.', 'فشل التأكيد.'));
    }
  };

  if (loading) return <div className="text-gray-400 text-sm p-8">{t('Loading…', 'جارٍ التحميل…')}</div>;
  if (!doc) return null;

  const fields = Object.entries(doc).filter(([k]) =>
    !['id', 'line_items', 'void_reason', 'voided_by', 'voided_at'].includes(k)
  );

  return (
    <div className="space-y-4 max-w-3xl">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{doc.document_number}</h2>
          <p className="text-sm text-gray-500">{doc.party_name}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={generatePDF} className="btn-secondary flex items-center gap-1 text-xs h-9">
            <Download size={14} />{t('Download PDF', 'تحميل PDF')}
          </button>
          {isFinance && doc.status === 'draft' && (
            <button onClick={confirmDoc} className="btn-primary flex items-center gap-1 text-xs h-9">
              <CheckCircle size={14} />{t('Confirm', 'تأكيد')}
            </button>
          )}
        </div>
      </div>

      {error && <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}

      {/* Tabs */}
      <div className="flex border-b border-gray-200 gap-1">
        {(['detail', 'audit'] as const).map((tab_) => (
          <button key={tab_} onClick={() => setTab(tab_)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === tab_ ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}>
            {tab_ === 'detail' ? t('Details', 'التفاصيل') : t('Audit Trail', 'سجل التدقيق')}
          </button>
        ))}
      </div>

      {tab === 'detail' && (
        <div className="card p-5 space-y-3">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {fields.map(([k, v]) => (
              <div key={k}>
                <span className="text-xs text-gray-400 uppercase tracking-wide">{k.replace(/_/g, ' ')}</span>
                <p className="text-gray-800 font-medium mt-0.5">
                  {v == null ? '—' : typeof v === 'boolean' ? (v ? '✓' : '✗') : String(v)}
                </p>
              </div>
            ))}
          </div>

          {/* Line items */}
          {doc.line_items?.length > 0 && (
            <div className="mt-4">
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">{t('Line Items', 'بنود الطلب')}</h4>
              <table className="w-full text-xs">
                <thead className="bg-gray-50"><tr>
                  <th className="text-left px-3 py-2">{t('Description', 'الوصف')}</th>
                  <th className="text-right px-3 py-2">{t('Qty', 'الكمية')}</th>
                  <th className="text-right px-3 py-2">{t('Unit Price', 'سعر الوحدة')}</th>
                  <th className="text-right px-3 py-2">{t('Total', 'الإجمالي')}</th>
                </tr></thead>
                <tbody className="divide-y divide-gray-50">
                  {doc.line_items.map((li: any) => (
                    <tr key={li.id}>
                      <td className="px-3 py-2">{li.description}</td>
                      <td className="px-3 py-2 text-right">{li.quantity}</td>
                      <td className="px-3 py-2 text-right">{formatAED(li.unit_price)}</td>
                      <td className="px-3 py-2 text-right font-medium">{formatAED(li.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Void action */}
          {isOwner && !doc.is_voided && (
            <div className="pt-4 border-t border-gray-100 space-y-2">
              <h4 className="text-xs font-semibold text-red-600 uppercase">{t('Void Document', 'إلغاء المستند')}</h4>
              <input value={voidReason} onChange={(e) => setVoidReason(e.target.value)}
                className="input text-sm" placeholder={t('Reason for voiding…', 'سبب الإلغاء…')} />
              <button onClick={voidDoc} className="btn-danger text-xs h-8 flex items-center gap-1">
                <Ban size={13} />{t('Void', 'إلغاء')}
              </button>
            </div>
          )}
        </div>
      )}

      {tab === 'audit' && (
        <div className="card divide-y divide-gray-50">
          {auditLog.length === 0 && (
            <p className="px-5 py-4 text-sm text-gray-400">{t('No audit entries.', 'لا توجد إدخالات تدقيق.')}</p>
          )}
          {auditLog.map((log: any) => (
            <div key={log.id} className="px-5 py-3 text-xs">
              <div className="flex justify-between">
                <span className="font-medium text-gray-700">{log.action}</span>
                <span className="text-gray-400">{formatDate(log.timestamp?.slice(0, 10))}</span>
              </div>
              {log.new_values && (
                <pre className="mt-1 text-gray-500 text-[10px] overflow-auto">{JSON.stringify(log.new_values, null, 2)}</pre>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
