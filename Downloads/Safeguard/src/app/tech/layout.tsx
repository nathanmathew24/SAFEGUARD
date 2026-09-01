import { TechBottomNav } from '@/components/tech/TechBottomNav';
import Link from 'next/link';
import { Shield, RefreshCw } from 'lucide-react';

export default function TechLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-[#0a0c12]">
      {/* Top bar */}
      <header className="sticky top-0 z-30 flex h-12 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-sidebar)] px-4 backdrop-blur-xl">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-500/20">
            <Shield className="size-3.5 text-indigo-400" />
          </div>
          <span className="text-xs font-semibold text-[var(--color-text-primary)]">Safeguard · Field</span>
        </div>
        <Link href="/" className="flex items-center gap-1 text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">
          <RefreshCw className="size-3" /> Switch portal
        </Link>
      </header>
      {/* Content — padded bottom for nav */}
      <main className="flex-1 pb-20">
        {children}
      </main>
      <TechBottomNav />
    </div>
  );
}
