import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, FileText, CreditCard, Upload, ClipboardList,
  ScrollText, Settings, LogOut, Globe, Menu, X, AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useLang } from '../contexts/LangContext';

const navItems = [
  { to: '/',               icon: LayoutDashboard, en: 'Dashboard',    ar: 'لوحة التحكم' },
  { to: '/invoices',       icon: FileText,        en: 'Invoices',     ar: 'الفواتير' },
  { to: '/pdc',            icon: CreditCard,      en: 'PDC',          ar: 'الشيكات' },
  { to: '/overdue',        icon: AlertTriangle,   en: 'Overdue',      ar: 'المتأخرات' },
  { to: '/upload',         icon: Upload,          en: 'Upload',       ar: 'رفع مستند' },
  { to: '/review-queue',   icon: ClipboardList,   en: 'Review Queue', ar: 'قيد المراجعة' },
  { to: '/audit',          icon: ScrollText,      en: 'Audit Log',    ar: 'سجل التدقيق',   ownerOnly: true },
  { to: '/settings',       icon: Settings,        en: 'Settings',     ar: 'الإعدادات',      ownerOnly: true },
];

export default function Layout() {
  const { user, logout, isOwner } = useAuth();
  const { toggle, t, dir } = useLang();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const items = navItems.filter((n) => !n.ownerOnly || isOwner);

  const Sidebar = () => (
    <nav className="flex flex-col h-full bg-brand-600 text-white w-56 shrink-0">
      <div className="px-4 py-5 border-b border-brand-700">
        <h1 className="text-lg font-bold tracking-tight">DocFlow</h1>
        <p className="text-xs text-brand-100 mt-0.5">{t('by Funoon.ai', 'بواسطة Funoon.ai')}</p>
      </div>

      <div className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {items.map(({ to, icon: Icon, en, ar }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-brand-700 text-white' : 'text-brand-100 hover:bg-brand-700 hover:text-white'
              }`
            }
            onClick={() => setSidebarOpen(false)}
          >
            <Icon size={16} />
            {t(en, ar)}
          </NavLink>
        ))}
      </div>

      <div className="p-3 border-t border-brand-700 space-y-1">
        <button
          onClick={toggle}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-brand-100 hover:bg-brand-700 hover:text-white transition-colors"
        >
          <Globe size={16} />
          {t('عربي', 'English')}
        </button>
        <button
          onClick={logout}
          className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm text-brand-100 hover:bg-red-700 hover:text-white transition-colors"
        >
          <LogOut size={16} />
          {t('Logout', 'تسجيل الخروج')}
        </button>
        <div className="px-3 py-2 text-xs text-brand-200 truncate">{user?.email}</div>
      </div>
    </nav>
  );

  return (
    <div className={`flex h-screen overflow-hidden ${dir === 'rtl' ? 'flex-row-reverse' : ''}`}>
      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-col">
        <Sidebar />
      </div>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="flex flex-col"><Sidebar /></div>
          <div className="flex-1 bg-black/40" onClick={() => setSidebarOpen(false)} />
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* Mobile topbar */}
        <div className="md:hidden flex items-center gap-3 px-4 py-3 bg-brand-600 text-white">
          <button onClick={() => setSidebarOpen(true)}><Menu size={20} /></button>
          <span className="font-bold">DocFlow</span>
        </div>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
