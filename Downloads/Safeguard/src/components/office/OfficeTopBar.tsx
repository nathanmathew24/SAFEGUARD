'use client';
// shadcn: Input, Button — top bar with search, notifications
import { Search, Bell, Link as LinkIcon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const pageLabels: Record<string, string> = {
  '/office/overview': 'Overview',
  '/office/buildings': 'Buildings',
  '/office/assets': 'Assets',
  '/office/schedule': 'Schedule',
  '/office/technicians': 'Technicians',
  '/office/reports': 'Reports',
  '/office/issues': 'Issues & Alerts',
  '/office/settings': 'Rules & Settings',
};

export function OfficeTopBar() {
  const pathname = usePathname();
  const label = Object.entries(pageLabels).find(([key]) => pathname === key || pathname.startsWith(key + '/'))?.[1] ?? 'Office';

  return (
    <header className="flex h-14 items-center gap-4 border-b border-[var(--color-border)] bg-[var(--color-sidebar)] px-6">
      <div className="flex-1">
        <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">{label}</h2>
      </div>
      {/* Search */}
      <div className="relative hidden sm:flex items-center">
        <Search className="absolute left-2.5 size-3.5 text-[var(--color-text-muted)]" />
        <input
          placeholder="Search buildings, assets…"
          className="h-8 w-52 rounded-lg border border-[var(--color-border)] bg-white/5 pl-8 pr-3 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-accent-primary)]/50 focus:bg-white/8 transition-colors"
        />
      </div>
      {/* Notifications */}
      <button className="relative flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors">
        <Bell className="size-4" />
        <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[var(--color-status-critical)] text-[8px] font-bold text-white">4</span>
      </button>
    </header>
  );
}
