import Link from 'next/link';
import { Shield, RefreshCw, FileText, Building2 } from 'lucide-react';

export default function OwnerLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0a0c12]">
      {/* Minimal top bar */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[var(--color-border)] bg-[var(--color-sidebar)] px-4 backdrop-blur-xl">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/20">
            <Shield className="size-4 text-indigo-400" />
          </div>
          <div>
            <span className="text-sm font-semibold text-[var(--color-text-primary)]">Safeguard</span>
            <span className="ml-1.5 text-xs text-[var(--color-text-muted)]">Owner Portal</span>
          </div>
        </div>
        {/* Owner nav */}
        <div className="flex items-center gap-1">
          <Link href="/owner/status" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:bg-white/5 hover:text-[var(--color-text-primary)] transition-colors">
            <Building2 className="size-3.5" /> Status
          </Link>
          <Link href="/owner/documents" className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:bg-white/5 hover:text-[var(--color-text-primary)] transition-colors">
            <FileText className="size-3.5" /> Documents
          </Link>
          <Link href="/" className="flex items-center gap-1 ml-2 text-[10px] text-[var(--color-text-subtle)] hover:text-[var(--color-text-muted)]">
            <RefreshCw className="size-3" /> Switch
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-2xl px-4 py-6">
        {children}
      </main>
    </div>
  );
}
