import React, { useEffect, useState, FormEvent } from 'react';
import { Save, Plus, Trash2 } from 'lucide-react';
import api from '../lib/api';
import { useLang } from '../contexts/LangContext';
import { useAuth } from '../contexts/AuthContext';

type Company = {
  name: string; trn: string; address: string;
  owner_whatsapp: string; finance_whatsapp: string;
  pdc_reminder_days_received: number; pdc_reminder_days_issued: number;
};

type User = { id: number; email: string; full_name: string; role: string; is_active: boolean; };

export default function Settings() {
  const { t } = useLang();
  const { isOwner } = useAuth();
  const [company, setCompany] = useState<Company | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  // New user form
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('staff');
  const [newPw, setNewPw] = useState('');
  const [userMsg, setUserMsg] = useState('');

  useEffect(() => {
    api.get('/company').then((r) => setCompany(r.data.data)).catch(() => {});
    api.get('/users').then((r) => setUsers(r.data.data ?? [])).catch(() => {});
  }, []);

  const saveCompany = async (e: FormEvent) => {
    e.preventDefault();
    if (!company) return;
    setSaving(true); setMsg('');
    try {
      await api.put('/company', company);
      setMsg(t('Saved successfully.', 'تم الحفظ بنجاح.'));
    } catch (err: any) {
      setMsg(err.response?.data?.message ?? t('Save failed.', 'فشل الحفظ.'));
    } finally { setSaving(false); }
  };

  const inviteUser = async (e: FormEvent) => {
    e.preventDefault();
    setUserMsg('');
    try {
      const r = await api.post('/users', { email: newEmail, full_name: newName, role: newRole, password: newPw });
      setUsers((prev) => [...prev, r.data.data]);
      setNewEmail(''); setNewName(''); setNewPw('');
      setUserMsg(t('User created.', 'تم إنشاء المستخدم.'));
    } catch (err: any) {
      setUserMsg(err.response?.data?.message ?? t('Failed.', 'فشل.'));
    }
  };

  const deactivate = async (uid: number) => {
    try {
      await api.patch(`/users/${uid}`, { is_active: false });
      setUsers((prev) => prev.map((u) => u.id === uid ? { ...u, is_active: false } : u));
    } catch { /* ignore */ }
  };

  if (!company) return <p className="text-sm text-gray-400">{t('Loading…', 'جارٍ التحميل…')}</p>;

  return (
    <div className="space-y-8 max-w-xl">
      <h2 className="text-xl font-semibold text-gray-900">{t('Settings', 'الإعدادات')}</h2>

      {/* Company profile */}
      <div className="card p-5 space-y-4">
        <h3 className="text-sm font-semibold text-gray-700">{t('Company Profile', 'بيانات الشركة')}</h3>
        <form onSubmit={saveCompany} className="space-y-3">
          {[
            { key: 'name', label: t('Company Name', 'اسم الشركة') },
            { key: 'trn',  label: t('TRN', 'رقم ضريبي') },
            { key: 'address', label: t('Address', 'العنوان') },
            { key: 'owner_whatsapp',  label: t('Owner WhatsApp', 'واتساب المالك') },
            { key: 'finance_whatsapp', label: t('Finance WhatsApp', 'واتساب المحاسبة') },
          ].map(({ key, label }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-500 mb-0.5">{label}</label>
              <input
                value={(company as any)[key] ?? ''}
                onChange={(e) => setCompany((c) => c ? { ...c, [key]: e.target.value } : c)}
                className="input text-sm"
                disabled={!isOwner}
              />
            </div>
          ))}

          <div className="grid grid-cols-2 gap-3">
            {[
              { key: 'pdc_reminder_days_received', label: t('Reminder days (received)', 'أيام تذكير (مستلم)') },
              { key: 'pdc_reminder_days_issued',   label: t('Reminder days (issued)', 'أيام تذكير (صادر)') },
            ].map(({ key, label }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-gray-500 mb-0.5">{label}</label>
                <input
                  type="number" min={1} max={30}
                  value={(company as any)[key] ?? ''}
                  onChange={(e) => setCompany((c) => c ? { ...c, [key]: parseInt(e.target.value, 10) } : c)}
                  className="input text-sm"
                  disabled={!isOwner}
                />
              </div>
            ))}
          </div>

          {isOwner && (
            <div className="flex items-center gap-3 pt-1">
              <button type="submit" disabled={saving} className="btn-primary flex items-center gap-2 text-sm">
                <Save size={14} />{saving ? t('Saving…', 'يُحفظ…') : t('Save', 'حفظ')}
              </button>
              {msg && <span className="text-xs text-gray-500">{msg}</span>}
            </div>
          )}
        </form>
      </div>

      {/* User management — owner only */}
      {isOwner && (
        <div className="card p-5 space-y-4">
          <h3 className="text-sm font-semibold text-gray-700">{t('Users', 'المستخدمون')}</h3>

          <div className="divide-y divide-gray-50">
            {users.map((u) => (
              <div key={u.id} className="py-2.5 flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-800">{u.full_name}</p>
                  <p className="text-xs text-gray-400">{u.email} · {u.role}</p>
                </div>
                {u.is_active ? (
                  <button onClick={() => deactivate(u.id)} className="btn-danger text-xs h-7 px-2 flex items-center gap-1">
                    <Trash2 size={11} />{t('Deactivate', 'إلغاء')}
                  </button>
                ) : (
                  <span className="text-xs text-gray-400">{t('Inactive', 'غير نشط')}</span>
                )}
              </div>
            ))}
          </div>

          <form onSubmit={inviteUser} className="border-t border-gray-100 pt-4 space-y-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase">{t('Add User', 'إضافة مستخدم')}</h4>
            <div className="grid grid-cols-2 gap-3">
              <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder={t('Full name', 'الاسم الكامل')} className="input text-sm" required />
              <input value={newEmail} onChange={(e) => setNewEmail(e.target.value)} placeholder={t('Email', 'البريد')} type="email" className="input text-sm" required />
              <select value={newRole} onChange={(e) => setNewRole(e.target.value)} className="input text-sm">
                <option value="staff">{t('Staff', 'موظف')}</option>
                <option value="finance_manager">{t('Finance Manager', 'مدير مالي')}</option>
                <option value="owner">{t('Owner', 'مالك')}</option>
              </select>
              <input value={newPw} onChange={(e) => setNewPw(e.target.value)} placeholder={t('Password', 'كلمة المرور')} type="password" className="input text-sm" required minLength={8} />
            </div>
            <div className="flex items-center gap-3">
              <button type="submit" className="btn-primary flex items-center gap-2 text-sm">
                <Plus size={14} />{t('Add', 'إضافة')}
              </button>
              {userMsg && <span className="text-xs text-gray-500">{userMsg}</span>}
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
