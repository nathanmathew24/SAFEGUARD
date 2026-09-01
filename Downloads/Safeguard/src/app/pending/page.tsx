'use client';

import { Shield, Clock } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Shown when a user is authenticated but their company's status is
 * PENDING or SUSPENDED — every API call returns a 403 in this state.
 * Redirect here from any page that catches a CompanyNotActiveError.
 */
export default function PendingPage() {
  const { signOut, user } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-8 text-center">
        <div className="flex flex-col items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--color-status-warning-bg)] ring-1 ring-[var(--color-status-warning)]/30">
            <Clock className="h-8 w-8 text-[var(--color-status-warning)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--color-text-primary)]">
              Your account is being set up
            </h1>
            <p className="mt-2 text-sm text-[var(--color-text-muted)]">
              JRHQ is reviewing your company's information. You'll receive
              a notification once your account is activated.
            </p>
          </div>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-white/[0.03] p-4 text-left space-y-2">
          <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-widest">Signed in as</p>
          <p className="text-sm text-[var(--color-text-primary)]">{user?.email}</p>
        </div>

        <div className="space-y-3">
          <button
            onClick={() => window.location.reload()}
            className="w-full rounded-xl border border-[var(--color-border)] bg-white/5 py-3 text-sm font-medium text-[var(--color-text-primary)] hover:bg-white/10 transition-colors"
          >
            Check again
          </button>
          <button
            onClick={signOut}
            className="w-full rounded-xl bg-white/5 py-3 text-sm font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
          >
            Sign out
          </button>
        </div>

        <div className="flex items-center justify-center gap-2">
          <Shield className="h-4 w-4 text-indigo-400" />
          <span className="text-xs text-[var(--color-text-subtle)]">Safeguard · UAE AMC Compliance Platform</span>
        </div>
      </div>
    </div>
  );
}
