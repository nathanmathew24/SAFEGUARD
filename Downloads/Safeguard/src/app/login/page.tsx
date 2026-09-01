'use client';

import { useState, type FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { Shield } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function LoginPage() {
  const { signIn } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const { error: signInError } = await signIn(email, password);

    if (signInError) {
      setError(signInError);
      setLoading(false);
      return;
    }

    // Supabase session is now set — middleware will allow through.
    router.push('/');
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/20 ring-1 ring-indigo-500/30">
            <Shield className="h-7 w-7 text-indigo-400" />
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Safeguard</h1>
            <p className="text-sm text-[var(--color-text-muted)]">UAE AMC Compliance Platform</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="block text-xs font-medium text-[var(--color-text-muted)]">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full rounded-xl border border-[var(--color-border)] bg-white/5 px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-accent-primary)]/50 transition-colors"
              placeholder="you@example.com"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="block text-xs font-medium text-[var(--color-text-muted)]">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-xl border border-[var(--color-border)] bg-white/5 px-4 py-3 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-accent-primary)]/50 transition-colors"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="rounded-xl bg-[var(--color-status-critical-bg)] px-4 py-3 text-sm text-[var(--color-status-critical)]">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-[var(--color-accent-primary)] py-3 text-sm font-semibold text-white hover:bg-[var(--color-accent-primary-hover)] disabled:opacity-60 transition-colors"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="text-center text-xs text-[var(--color-text-subtle)]">
          Account access is managed by your administrator.
        </p>
      </div>
    </div>
  );
}
