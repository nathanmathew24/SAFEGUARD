import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Download } from 'lucide-react';
import api, { formatAED, formatDate } from '../lib/api';
import { useLang } from '../contexts/LangContext';
import { useAuth } from '../contexts/AuthContext';

const DOC_LABELS: Record<string, { en: string; ar: string }> = {
  invoices:          { en: 'Sales Invoices', ar: 'فواتير المبيعات' },
  'purchase-invoices': { en: 'Purchase Invoices', ar: 'فواتير المشتريات' },
  lpos:              { en: 'Purchase Orders', ar: 'أوامر الشراء' },
  quotations:        { en: 'Quotations', ar: 'عروض الأسعار' },
  'credit-notes':    { en: 'Credit Notes', ar: 'إشعارات دائن' },
  'debit-notes':     { en: 'Debit Notes', ar: 'إشعارات مدين' },
  'delivery-notes':  { en: 'Delivery Notes', ar: 'مذكرات التسليم' },
  'receipt-vouchers':{ en: 'Receipt Vouchers', ar: 'سندات القبض' },
};

const PAGE_SIZE = 25;

function StatusBadge({ status }: { status: string }) {
  const cls: Record<string, string> = {
    draft: 'badge-draft', confirmed: 'badge-confirmed', voided: 'badge-voided',
  };
  return <span className={cls[status] ?? 'badge-draft'}>{status}</span>;
}

export default function DocumentList() {
  const { docType = 'invoices' } = useParams<{ docType: string }>();
  const { t } = useLang();
  const { isFinance } = useAuth();
  const [docs, setDocs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [search, setSearch] = useState('');

  const label = DOC_LABELS[docType] ?? { en: docType, ar: docType };

  useEffect(() => {
    setLoading(true);
    api.get(`/${docType}`, { params: { page, per_page: PAGE_SIZE, status: statusFilter || undefined } })
      .then((r) => setDocs(r.data.data ?? []))
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, [docType, page, statusFilter]);

  const filtered = search
    ? docs.filter((d) =>
        d.document_number?.toLowerCase().includes(search.toLowerCase()) ||
        d.party_name?.toLowerCase().includes(search.toLowerCase()))
    : docs;

  const exportCSV = () => {
    const rows = [
      ['Number', 'Party', 'Date', 'Amount', 'Status'],
      ...filtered.map((d) => [d.document_number, d.party_name, d.document_date,
        d.total_amount != null ? (d.total_amount / 100).toFixed(2) : '', d.status]),
    ];
    const csv = rows.map((r) => r.join(',')).join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    a.download = `${docType}.csv`;
    a.click();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-xl font-semibold text-gray-900">{t(label.en, label.ar)}</h2>
        <div className="flex items-center gap-2 flex-wrap">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('Search…', 'بحث…')}
            className="input w-44 h-9 text-xs"
          />
          <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="input w-36 h-9 text-xs">
            <option value="">{t('All Status', 'جميع الحالات')}</option>
            <option value="draft">{t('Draft', 'مسودة')}</option>
            <option value="confirmed">{t('Confirmed', 'مؤكد')}</option>
            <option value="voided">{t('Voided', 'ملغى')}</option>
          </select>
          {isFinance && (
            <button onClick={exportCSV} className="btn-secondary h-9 flex items-center gap-1 text-xs">
              <Download size={14} />{t('Export', 'تصدير')}
            </button>
          )}
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{t('Number', 'الرقم')}</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{t('Party', 'الطرف')}</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{t('Date', 'التاريخ')}</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{t('Amount', 'المبلغ')}</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">{t('Status', 'الحالة')}</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">{t('Loading…', 'جارٍ التحميل…')}</td></tr>
              )}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">{t('No documents found.', 'لا توجد مستندات.')}</td></tr>
              )}
              {filtered.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{doc.document_number}</td>
                  <td className="px-4 py-3 text-gray-800 max-w-[180px] truncate">{doc.party_name}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(doc.document_date)}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-800">
                    {doc.total_amount != null ? formatAED(doc.total_amount) : '—'}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={doc.status} /></td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/${docType}/${doc.id}`} className="text-xs text-brand-600 hover:underline">{t('View', 'عرض')}</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
            className="flex items-center gap-1 disabled:opacity-40 hover:text-gray-800">
            <ChevronLeft size={14} />{t('Prev', 'السابق')}
          </button>
          <span>{t(`Page ${page}`, `صفحة ${page}`)}</span>
          <button disabled={filtered.length < PAGE_SIZE} onClick={() => setPage((p) => p + 1)}
            className="flex items-center gap-1 disabled:opacity-40 hover:text-gray-800">
            {t('Next', 'التالي')}<ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
