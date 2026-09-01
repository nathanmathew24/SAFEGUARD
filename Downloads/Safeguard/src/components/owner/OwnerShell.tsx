import Link from "next/link";
import { Shield, Building2 } from "lucide-react";

export function OwnerShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="h-14 flex items-center justify-between px-6 border-b border-white/[0.06] bg-[var(--color-sidebar)] sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-[var(--color-accent-primary)]" />
          <span className="text-sm font-semibold text-[var(--color-text-primary)]">
            Safeguard
          </span>
        </div>
        <nav className="flex items-center gap-1">
          <Link
            href="/status"
            className="px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] rounded-lg hover:bg-white/[0.05] transition-colors flex items-center gap-1.5"
          >
            <Building2 className="w-3.5 h-3.5" />
            Status
          </Link>
          <Link
            href="/documents"
            className="px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            Documents
          </Link>
        </nav>
        <Link
          href="/"
          className="text-xs text-[var(--color-text-subtle)] hover:text-[var(--color-text-muted)] transition-colors"
        >
          ← Portals
        </Link>
      </header>
      <main className="max-w-2xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
