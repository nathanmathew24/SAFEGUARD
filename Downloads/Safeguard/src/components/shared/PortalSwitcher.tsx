'use client';
// shadcn: Card, Button — Portal role selector shown on root page
import { useRouter } from 'next/navigation';
import { Shield, HardHat, Building2 } from 'lucide-react';

const portals = [
  {
    role: 'office',
    href: '/office/overview',
    icon: Shield,
    title: 'Office Admin',
    subtitle: 'Full portfolio management, schedule, reports & rules',
    color: 'from-indigo-500/20 to-indigo-600/5',
    iconColor: 'text-indigo-400',
    border: 'border-indigo-500/20 hover:border-indigo-500/50',
  },
  {
    role: 'tech',
    href: '/tech/jobs',
    icon: HardHat,
    title: 'Technician',
    subtitle: 'Field inspection app — today\'s jobs, checklists, evidence capture',
    color: 'from-amber-500/20 to-amber-600/5',
    iconColor: 'text-amber-400',
    border: 'border-amber-500/20 hover:border-amber-500/50',
  },
  {
    role: 'owner',
    href: '/owner/status',
    icon: Building2,
    title: 'Building Owner',
    subtitle: 'Compliance status & document access for your property',
    color: 'from-emerald-500/20 to-emerald-600/5',
    iconColor: 'text-emerald-400',
    border: 'border-emerald-500/20 hover:border-emerald-500/50',
  },
];

export function PortalSwitcher() {
  const router = useRouter();

  const handleSelect = (href: string, role: string) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('safeguard-role', role);
    }
    router.push(href);
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 p-6">
      {/* Logo */}
      <div className="flex flex-col items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/20 ring-1 ring-indigo-500/30">
          <Shield className="h-7 w-7 text-indigo-400" />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Safeguard</h1>
          <p className="text-sm text-[var(--color-text-muted)]">UAE AMC Compliance Platform · Emirates Safety Systems</p>
        </div>
      </div>

      {/* Portal selection */}
      <div className="w-full max-w-2xl">
        <p className="mb-4 text-center text-xs font-medium uppercase tracking-widest text-[var(--color-text-subtle)]">
          Select Portal
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          {portals.map((portal) => {
            const Icon = portal.icon;
            return (
              <button
                key={portal.role}
                onClick={() => handleSelect(portal.href, portal.role)}
                className={`group flex flex-1 flex-col gap-3 rounded-2xl border bg-gradient-to-b ${portal.color} ${portal.border} p-5 text-left transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-black/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500`}
              >
                <div className={`flex h-10 w-10 items-center justify-center rounded-xl bg-black/20 ${portal.iconColor}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-semibold text-[var(--color-text-primary)]">{portal.title}</p>
                  <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{portal.subtitle}</p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <p className="text-center text-xs text-[var(--color-text-subtle)]">
        Emirates Safety Systems · UAE AMC Compliance Platform
      </p>
    </div>
  );
}
