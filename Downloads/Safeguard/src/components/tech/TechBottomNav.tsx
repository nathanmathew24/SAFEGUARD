'use client';
// shadcn: Badge — mobile bottom nav for technician portal
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Briefcase, RefreshCw, History, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

const nav = [
  { href: '/tech/jobs', label: 'Jobs', icon: Briefcase },
  { href: '/tech/sync', label: 'Sync', icon: RefreshCw },
  { href: '/tech/history', label: 'History', icon: History },
];

export function TechBottomNav() {
  const pathname = usePathname();
  return (
    <nav className="safe-bottom fixed bottom-0 left-0 right-0 z-40 flex border-t border-[var(--color-border)] bg-[var(--color-sidebar)] backdrop-blur-xl">
      {nav.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(href + '/') && href !== '/tech/jobs' || pathname === href;
        const isActive = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              'flex flex-1 flex-col items-center gap-0.5 py-3 text-[10px] font-medium transition-colors',
              isActive ? 'text-[var(--color-accent-primary)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
            )}
          >
            <Icon className={cn('size-5', isActive ? 'text-[var(--color-accent-primary)]' : '')} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
