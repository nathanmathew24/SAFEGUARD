'use client';
// shadcn: Input — History: past completed jobs, searchable, read-only
// Screen 6 (Tech) — History: past completed jobs for this technician
import { useState } from 'react';
import Link from 'next/link';
import { visits, getBuildingById, getResultsByVisit } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { formatDate } from '@/lib/utils';
import { Search, CheckCircle2, XCircle, Calendar } from 'lucide-react';

const CURRENT_TECH = 'tech-001';

export default function TechHistoryPage() {
  const [search, setSearch] = useState('');

  const completedVisits = visits
    .filter(v => v.technicianId === CURRENT_TECH && v.status === 'completed')
    .sort((a, b) => new Date(b.scheduledDate).getTime() - new Date(a.scheduledDate).getTime());

  const filtered = completedVisits.filter(v => {
    if (!search) return true;
    const building = getBuildingById(v.buildingId);
    return (
      building?.name.toLowerCase().includes(search.toLowerCase()) ||
      v.scheduledDate.includes(search)
    );
  });

  // Group by week label
  const grouped: Record<string, typeof filtered> = {};
  filtered.forEach(v => {
    const date = new Date(v.scheduledDate);
    const weekStart = new Date(date);
    weekStart.setDate(date.getDate() - date.getDay());
    const key = `Week of ${weekStart.toLocaleDateString('en-AE', { day: 'numeric', month: 'short', year: 'numeric' })}`;
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(v);
  });

  return (
    <div className="px-4 py-5 space-y-4">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text-primary)]">History</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Past completed inspections — read only</p>
      </div>

      {/* Search */}
      <div className="relative flex items-center">
        <Search className="absolute left-3 size-4 text-[var(--color-text-muted)]" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search by building or date…"
          className="w-full rounded-xl border border-[var(--color-border)] bg-white/5 py-3 pl-10 pr-4 text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-accent-primary)]/50 transition-colors"
        />
      </div>

      {Object.keys(grouped).length === 0 ? (
        <div className="py-16 text-center">
          <Calendar className="mx-auto size-10 text-[var(--color-text-subtle)] mb-3" />
          <p className="text-sm text-[var(--color-text-muted)]">No completed jobs found.</p>
        </div>
      ) : (
        Object.entries(grouped).map(([week, weekVisits]) => (
          <div key={week}>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-[var(--color-text-subtle)]">{week}</p>
            <div className="space-y-2">
              {weekVisits.map(v => {
                const building = getBuildingById(v.buildingId);
                const results = getResultsByVisit(v.id);
                const passCount = results.filter(r => r.pass).length;
                const failCount = results.filter(r => !r.pass).length;
                return (
                  <GlassCard key={v.id} padding="md" className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-status-ok-bg)] shrink-0">
                      <CheckCircle2 className="size-5 text-[var(--color-status-ok)]" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-[var(--color-text-primary)] text-sm truncate">{building?.name}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <TradeBadge trade={v.trade} size="sm" />
                        <span className="text-[11px] text-[var(--color-text-muted)]">{formatDate(v.scheduledDate)}</span>
                      </div>
                    </div>
                    {results.length > 0 && (
                      <div className="flex items-center gap-2 text-xs shrink-0">
                        {passCount > 0 && <span className="flex items-center gap-0.5 text-[var(--color-status-ok)]"><CheckCircle2 className="size-3" />{passCount}</span>}
                        {failCount > 0 && <span className="flex items-center gap-0.5 text-[var(--color-status-critical)]"><XCircle className="size-3" />{failCount}</span>}
                      </div>
                    )}
                  </GlassCard>
                );
              })}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
