import React, { useEffect, useState } from 'react';
import api, { formatDate } from '../lib/api';
import { useLang } from '../contexts/LangContext';

const TABLES = ['invoices', 'purchase_invoices', 'lpos', 'quotations', 'credit_notes',
  'debit_notes', 'delivery_notes', 'receipt_vouchers', 'pdcs', 'users', 'companies'];

const ACTION_COLORS: Record<string, string> = {
  CREATE: 'bg-green-100 text-green-700',
  UPDATE: 'bg-blue-100 text-blue-700',
  DELETE: 'bg-red-100 text-red-700',
  VIEW:   'bg-gray-100 text-gray-600',
};

export default function AuditLog() {
  const { t } = useLang();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [table, setTable] = useState('');

  useEffect(() => {
    setLoading(true);
    api.get('/audit-log', { params: { page, per_page: 50, table_name: table || undefined } })
      .then((r) => setLogs(r.data.data ?? []))
      .finally(() => setLoading(false));
  }, [page, table]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-xl font-semibold text-gray-900">{t('Audit Log', 'سجل التدقيق')}</h2>
        <select value={table} onChange={(e) => { setTable(e.target.value); setPage(1); }} className="input w-48 h-9 text-xs">
          <option value="">{t('All Tables', 'جميع الجداول')}</option>
          {TABLES.map((tb) => <option key={tb} value={tb}>{tb.replace(/_/g, ' ')}</option>)}
        </select>
      </div>

      <div className="card divide-y divide-gray-50">
        {loading && (
          <p className="px-5 py-8 text-center text-gray-400 text-sm">{t('Loading…', 'جارٍ التحميل…')}</p>
        )}
        {!loading && logs.length === 0 && (
          <p className="px-5 py-8 text-center text-gray-400 text-sm">{t('No entries found.', 'لا توجد إدخالات.')}</p>
        )}
        {logs.map((log: any) => (
          <div key={log.id} className="px-5 py-3">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${ACTION_COLORS[log.action] ?? 'bg-gray-100 text-gray-600'}`}>
                  {log.action}
                </span>
                <span className="text-xs font-mono text-gray-600">{log.table_name}#{log.record_id}</span>
                <span className="text-xs text-gray-400">by {log.user_id ?? 'system'}</span>
                {log.ip_address && <span className="text-xs text-gray-300">{log.ip_address}</span>}
              </div>
              <span className="text-xs text-gray-400 shrink-0">{formatDate(log.timestamp?.slice(0, 10))}</span>
            </div>
            {log.new_values && Object.keys(log.new_values).length > 0 && (
              <pre className="mt-1.5 text-[10px] text-gray-400 overflow-auto max-h-20 bg-gray-50 rounded p-2">
                {JSON.stringify(log.new_values, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 px-1">
        <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
          className="hover:text-gray-800 disabled:opacity-40">
          ← {t('Prev', 'السابق')}
        </button>
        <span>{t(`Page ${page}`, `صفحة ${page}`)}</span>
        <button disabled={logs.length < 50} onClick={() => setPage((p) => p + 1)}
          className="hover:text-gray-800 disabled:opacity-40">
          {t('Next', 'التالي')} →
        </button>
      </div>
    </div>
  );
}
