'use client';
// shadcn: Avatar, DropdownMenu, Separator — glass sidebar with workspace switcher and nav
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Building2, Database, CalendarDays,
  Users, FileText, AlertTriangle, Settings, Shield,
  ChevronDown, LogOut, User, RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const mainNav = [
  { href: '/office/overview', label: 'Overview', icon: LayoutDashboard },
  { href: '/office/buildings', label: 'Buildings', icon: Building2 },
  { href: '/office/assets', label: 'Assets', icon: Database },
  { href: '/office/schedule', label: 'Schedule', icon: CalendarDays },
  { href: '/office/technicians', label: 'Technicians', icon: Users },
];

const complianceNav = [
  { href: '/office/reports', label: 'Reports', icon: FileText },
  { href: '/office/issues', label: 'Issues & Alerts', icon: AlertTriangle },
  { href: '/office/settings', label: 'Rules & Settings', icon: Settings },
];

function NavItem({ href, label, icon: Icon }: { href: string; label: string; icon: React.ComponentType<{ className?: string }> }) {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(href + '/');
  return (
    <Link
      href={href}
      className={cn(
        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all',
        active
          ? 'bg-[var(--color-accent-primary)]/15 text-[var(--color-accent-primary)] font-medium'
          : 'text-[var(--color-text-muted)] hover:bg-white/5 hover:text-[var(--color-text-primary)]'
      )}
    >
      <Icon className="size-4 shrink-0" />
      {label}
    </Link>
  );
}

export function OfficeSidebar() {
  return (
    <aside className="glass-sidebar flex h-screen w-60 flex-col py-4">
      {/* Workspace switcher */}
      <div className="px-3 pb-4">
        <button className="flex w-full items-center gap-2.5 rounded-xl bg-white/5 px-3 py-2.5 text-left hover:bg-white/8 transition-colors">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20">
            <Shield className="size-3.5 text-indigo-400" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-semibold text-[var(--color-text-primary)]">Emirates Safety Systems</p>
            <p className="text-[10px] text-[var(--color-text-muted)]">Dubai · Workspace</p>
          </div>
          <ChevronDown className="size-3.5 text-[var(--color-text-muted)] shrink-0" />
        </button>
      </div>

      {/* Main nav */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3">
        {mainNav.map((item) => <NavItem key={item.href} {...item} />)}

        <div className="py-3">
          <p className="px-3 pb-1.5 text-[10px] font-semibold uppercase tracking-widest text-[var(--color-text-subtle)]">
            Compliance Desk
          </p>
          {complianceNav.map((item) => <NavItem key={item.href} {...item} />)}
        </div>
      </nav>

      {/* User */}
      <div className="mt-auto border-t border-[var(--color-border)] px-3 pt-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500/20 text-xs font-bold text-indigo-400">
            AF
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-[var(--color-text-primary)]">Admin · Farzeel</p>
            <p className="text-[10px] text-[var(--color-text-muted)]">Office Portal</p>
          </div>
          <Link href="/" className="rounded-md p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors" title="Switch portal">
            <RefreshCw className="size-3.5" />
          </Link>
        </div>
      </div>
    </aside>
  );
}
