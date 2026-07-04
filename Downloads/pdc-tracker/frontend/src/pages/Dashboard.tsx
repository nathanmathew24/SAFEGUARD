import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, AlertTriangle, CreditCard, ClipboardList } from 'lucide-react';
import api, { formatAED, formatDate } from '../lib/api';
import { useLang } from '../contexts/LangContext';
import { useAuth } from '../contexts/AuthContext';

interface SummaryCard { label: string; labelAr: string; value: string | number; icon: React.ReactNode; href: string; color: string; }

function StatCard({ label, labelAr, value, icon, href, color }: SummaryCard) {
  const { t } = useLang();
  return (
    <Link to={href} className={`card p-5 flex items-center gap-4 hover:shadow-md transition-shadow`}>
      <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{t(label, labelAr)}</p>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const { t } = useLang();
  const { isFinance } = useAuth();
  const [overdue, setOverdue] = useState<any[]>([]);
  const [pdcDue, setPdcDue] = useState<any[]>([]);
  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [reviewCount, setReviewCount] = useState(0);

  useEffect(() => {
    if (isFinance) {
      api.get('/pdc/payments/overdue').then((r) => setOverdue(r.data.data ?? [])).catch(() => {});
      api.get('/review-queue').then((r) => setReviewCount(r.data.data?.length ?? 0)).catch(() => {});
    }
    api.get('/pdc/received').then((r) => {
      const soon = (r.data.data ?? []).filter((p: any) => {
        const days = Math.round((new Date(p.cheque_date).getTime() - Date.now()) / 86400000);
        return days >= 0 && days <= 7 && p.pdc_status === 'pending';
      });
      setPdcDue(soon);
    }).catch(() => {});
    api.get('/audit-log?limit=10').then((r) => setAuditLog(r.data.data ?? [])).catch(() => {});
  }, [isFinance]);

  const cards: SummaryCard[] = [
    { label: 'Overdue Payments', labelAr: 'مدفوعات متأخرة', value: overdue.length, icon: <AlertTriangle size={20} className="text-red-600" />, href: '/overdue', color: 'bg-red-50' },
    { label: 'PDCs Due This Week', labelAr: 'شيكات هذا الأسبوع', value: pdcDue.length, icon: <CreditCard size={20} className="text-amber-600" />, href: '/pdc', color: 'bg-amber-50' },
    { label: 'Pending Review', labelAr: 'قيد المراجعة', value: reviewCount, icon: <ClipboardList size={20} className="text-blue-600" />, href: '/review-queue', color: 'bg-blue-50' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">{t('Dashboard', 'لوحة التحكم')}</h2>

      {isFinance && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {cards.map((c) => <StatCard key={c.href} {...c} />)}
        </div>
      )}

      {/* Quick actions */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{t('Quick Actions', 'إجراءات سريعة')}</h3>
        <div className="flex flex-wrap gap-3">
          <Link to="/upload" className="btn-primary flex items-center gap-2"><FileText size={15} />{t('Upload Document', 'رفع مستند')}</Link>
          <Link to="/invoices" className="btn-secondary">{t('View Invoices', 'عرض الفواتير')}</Link>
          <Link to="/pdc" className="btn-secondary">{t('PDC Schedule', 'جدول الشيكات')}</Link>
        </div>
      </div>

      {/* Recent activity */}
      <div className="card">
        <div className="px-5 py-4 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700">{t('Recent Activity', 'النشاط الأخير')}</h3>
        </div>
        <div className="divide-y divide-gray-50">
          {auditLog.length === 0 && (
            <p className="px-5 py-4 text-sm text-gray-400">{t('No activity yet.', 'لا يوجد نشاط حتى الآن.')}</p>
          )}
          {auditLog.map((log: any) => (
            <div key={log.id} className="px-5 py-3 flex items-center justify-between gap-4">
              <div>
                <span className="text-xs font-medium text-gray-800">{log.action}</span>
                <span className="text-xs text-gray-400 mx-2">·</span>
                <span className="text-xs text-gray-500">{log.table_name}</span>
              </div>
              <span className="text-xs text-gray-400 shrink-0">{formatDate(log.timestamp?.slice(0, 10))}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
