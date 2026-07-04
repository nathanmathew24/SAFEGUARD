import React, { useEffect, useState } from 'react';
import api, { formatAED, formatDate, daysUntil } from '../lib/api';
import { useLang } from '../contexts/LangContext';
import { useAuth } from '../contexts/AuthContext';

type PDC = {
  id: number; party_name: string; amount: number; cheque_date: string;
  bank_name: string; cheque_number: string; pdc_status: string; pdc_direction: string;
};

function urgencyColor(days: number): string {
  if (days < 0) return 'border-red-400 bg-red-50';
  if (days <= 3) return 'border-red-300 bg-red-50';
  if (days <= 7) return 'border-amber-300 bg-amber-50';
  return 'border-green-300 bg-green-50';
}

function PDCCard({ pdc, onAction, isFinance, isOwner }: {
  pdc: PDC; onAction: (id: number, action: string) => void; isFinance: boolean; isOwner: boolean;
}) {
  const { t } = useLang();
  const days = daysUntil(pdc.cheque_date);

  return (
    <div className={`border-l-4 rounded-lg p-4 ${urgencyColor(days)}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="font-semibold text-gray-800 text-sm">{pdc.party_name}</p>
          <p className="text-xl font-bold text-gray-900 mt-0.5">{formatAED(pdc.amount)}</p>
        </div>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
          days < 0 ? 'bg-red-100 text-red-700' : days <= 3 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
        }`}>
          {days < 0 ? `${Math.abs(days)}d overdue` : days === 0 ? 'Today' : `${days}d left`}
        </span>
      </div>
      <div className="mt-2 text-xs text-gray-500 space-y-0.5">
        <p>{t('Bank:', 'البنك:')} {pdc.bank_name}</p>
        <p>{t('Cheque #:', 'رقم الشيك:')} {pdc.cheque_number}</p>
        <p>{t('Due:', 'الاستحقاق:')} {formatDate(pdc.cheque_date)}</p>
      </div>
      {pdc.pdc_status === 'pending' && (
        <div className="mt-3 flex gap-2 flex-wrap">
          {isFinance && (
            <button onClick={() => onAction(pdc.id, 'mark-submitted')}
              className="btn-secondary text-xs h-7 px-3">
              {t('Submit', 'تقديم')}
            </button>
          )}
        </div>
      )}
      {pdc.pdc_status === 'submitted' && (
        <div className="mt-3 flex gap-2 flex-wrap">
          {isFinance && (
            <button onClick={() => onAction(pdc.id, 'mark-cleared')}
              className="btn-primary text-xs h-7 px-3">
              {t('Clear', 'تسوية')}
            </button>
          )}
          {isOwner && (
            <button onClick={() => onAction(pdc.id, 'mark-bounced')}
              className="btn-danger text-xs h-7 px-3">
              {t('Bounced', 'مرتجع')}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function PDCDashboard() {
  const { t } = useLang();
  const { isFinance, isOwner } = useAuth();
  const [received, setReceived] = useState<PDC[]>([]);
  const [issued, setIssued] = useState<PDC[]>([]);
  const [tab, setTab] = useState<'received' | 'issued'>('received');
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    Promise.all([
      api.get('/pdc/received').then((r) => setReceived(r.data.data ?? [])),
      api.get('/pdc/issued').then((r) => setIssued(r.data.data ?? [])),
    ]).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleAction = async (id: number, action: string) => {
    try {
      await api.post(`/pdc/${id}/${action}`);
      load();
    } catch (e: any) {
      alert(e.response?.data?.message ?? 'Action failed');
    }
  };

  const list = tab === 'received' ? received : issued;
  const upcoming = list.filter((p) => p.pdc_status === 'pending' && daysUntil(p.cheque_date) >= 0);
  const overdue  = list.filter((p) => p.pdc_status === 'pending' && daysUntil(p.cheque_date) < 0);
  const cleared  = list.filter((p) => ['cleared', 'bounced', 'cancelled'].includes(p.pdc_status));

  const col = (title: string, titleAr: string, items: PDC[]) => (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold text-gray-500 uppercase">{t(title, titleAr)} ({items.length})</h3>
      {items.length === 0 && <p className="text-xs text-gray-400">{t('None', 'لا يوجد')}</p>}
      {items.map((p) => (
        <PDCCard key={p.id} pdc={p} onAction={handleAction} isFinance={isFinance} isOwner={isOwner} />
      ))}
    </div>
  );

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900">{t('PDC Dashboard', 'لوحة الشيكات')}</h2>

      <div className="flex border-b border-gray-200 gap-1">
        {(['received', 'issued'] as const).map((t_) => (
          <button key={t_} onClick={() => setTab(t_)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t_ ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}>
            {t_ === 'received' ? t('Received', 'مستلمة') : t('Issued', 'صادرة')}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-sm text-gray-400">{t('Loading…', 'جارٍ التحميل…')}</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {col('Upcoming (next 30d)', 'قادمة (30 يوم)', upcoming)}
          {col('Overdue', 'متأخرة', overdue)}
          {col('Cleared / Bounced', 'تم تسويتها', cleared)}
        </div>
      )}
    </div>
  );
}
