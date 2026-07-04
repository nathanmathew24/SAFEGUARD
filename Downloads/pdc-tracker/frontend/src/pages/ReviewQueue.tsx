import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Edit2 } from 'lucide-react';
import api, { formatDate } from '../lib/api';
import { useLang } from '../contexts/LangContext';

function QueueList() {
  const { t } = useLang();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/review-queue').then((r) => setItems(r.data.data ?? [])).finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-gray-400">{t('Loading…', 'جارٍ التحميل…')}</p>;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">{t('Review Queue', 'قائمة المراجعة')}</h2>
      {items.length === 0 && (
        <div className="card p-8 text-center text-gray-400 text-sm">
          {t('No documents pending review.', 'لا توجد مستندات قيد المراجعة.')}
        </div>
      )}
      <div className="space-y-2">
        {items.map((item) => (
          <Link key={item.id} to={`/review-queue/${item.id}`}
            className="card px-5 py-4 flex items-center justify-between hover:shadow-md transition-shadow">
            <div>
              <p className="text-sm font-semibold text-gray-800">{item.extracted_data?.document_number ?? `#${item.id}`}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {item.extracted_data?.party_name ?? '—'} · {item.extracted_data?.doc_type ?? '—'} · {formatDate(item.created_at?.slice(0, 10))}
              </p>
            </div>
            <span className="text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
              {t('Pending', 'قيد المراجعة')}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

function QueueDetail() {
  const { id } = useParams<{ id: string }>();
  const { t } = useLang();
  const navigate = useNavigate();
  const [item, setItem] = useState<any>(null);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get(`/review-queue/${id}`).then((r) => {
      const data = r.data.data;
      setItem(data);
      setFields(data.extracted_data ?? {});
    }).finally(() => setLoading(false));
  }, [id]);

  const submit = async (action: 'approve' | 'reject') => {
    setError('');
    try {
      await api.post(`/review-queue/${id}/${action}`, { extracted_data: fields });
      navigate('/review-queue');
    } catch (e: any) {
      setError(e.response?.data?.message ?? t('Action failed.', 'فشل الإجراء.'));
    }
  };

  if (loading) return <p className="text-sm text-gray-400">{t('Loading…', 'جارٍ التحميل…')}</p>;
  if (!item) return null;

  const editableFields = ['doc_type', 'document_number', 'party_name', 'document_date', 'total_amount', 'vat_amount', 'payment_method'];

  return (
    <div className="space-y-4 max-w-xl">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate('/review-queue')} className="text-sm text-gray-400 hover:text-gray-700">← {t('Back', 'رجوع')}</button>
        <h2 className="text-xl font-semibold text-gray-900">{t('Review Document', 'مراجعة المستند')}</h2>
      </div>

      {error && (
        <div className="px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
      )}

      <div className="card p-5 space-y-3">
        <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
          <Edit2 size={12} />{t('Editable fields — correct before approving', 'حقول قابلة للتعديل')}
        </div>
        {editableFields.map((f) => (
          <div key={f}>
            <label className="block text-xs font-medium text-gray-500 uppercase mb-0.5">{f.replace(/_/g, ' ')}</label>
            <input
              value={fields[f] ?? ''}
              onChange={(e) => setFields((prev) => ({ ...prev, [f]: e.target.value }))}
              className="input text-sm"
            />
          </div>
        ))}
      </div>

      <div className="flex gap-3">
        <button onClick={() => submit('approve')} className="btn-primary flex items-center gap-2">
          <CheckCircle size={15} />{t('Approve', 'موافقة')}
        </button>
        <button onClick={() => submit('reject')} className="btn-danger flex items-center gap-2">
          <XCircle size={15} />{t('Reject', 'رفض')}
        </button>
      </div>
    </div>
  );
}

export function ReviewQueueDetail() { return <QueueDetail />; }
export default QueueList;
