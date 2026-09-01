// shadcn: Card, Badge, Avatar — Technicians roster
// Screen 5 — Technicians: grid of technician cards with trade qualifications and job load
import { technicians, visits, getVisitsByTechnician } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { VisitStatusBadge } from '@/components/shared/VisitStatusBadge';
import { getBuildingById } from '@/lib/mockData';
import { formatDate } from '@/lib/utils';
import { Phone, Mail, Briefcase } from 'lucide-react';

const TODAY = '2026-09-01';

export default function TechniciansPage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2">
        {technicians.map(tech => {
          const techVisits = getVisitsByTechnician(tech.id);
          const upcomingVisits = techVisits.filter(v =>
            v.scheduledDate >= TODAY && (v.status === 'scheduled' || v.status === 'in-progress')
          );
          const recentVisits = techVisits.filter(v => v.status === 'completed').slice(0, 3);

          return (
            <GlassCard key={tech.id} padding="md" className="flex flex-col gap-4">
              {/* Header */}
              <div className="flex items-start gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/20 text-base font-bold text-indigo-400 shrink-0">
                  {tech.initials}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-[var(--color-text-primary)]">{tech.name}</p>
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {tech.trades.map(t => <TradeBadge key={t} trade={t} size="sm" />)}
                  </div>
                </div>
                <div className="flex items-center gap-1.5 rounded-full bg-[var(--color-accent-glow)] px-2 py-1">
                  <Briefcase className="size-3 text-[var(--color-accent-primary)]" />
                  <span className="text-xs font-medium text-[var(--color-accent-primary)]">{tech.activeJobCount} active</span>
                </div>
              </div>

              {/* Contact */}
              <div className="space-y-1 text-xs text-[var(--color-text-muted)]">
                <div className="flex items-center gap-1.5"><Phone className="size-3" />{tech.phone}</div>
                <div className="flex items-center gap-1.5"><Mail className="size-3" />{tech.email}</div>
              </div>

              {/* Upcoming visits */}
              {upcomingVisits.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-[var(--color-text-muted)]">Upcoming ({upcomingVisits.length})</p>
                  <div className="space-y-1">
                    {upcomingVisits.slice(0, 3).map(v => {
                      const building = getBuildingById(v.buildingId);
                      return (
                        <div key={v.id} className="flex items-center gap-2 rounded-lg bg-white/[0.02] px-2.5 py-1.5">
                          <TradeBadge trade={v.trade} size="sm" showIcon={false} />
                          <span className="flex-1 truncate text-xs text-[var(--color-text-primary)]">{building?.name}</span>
                          <span className="text-[11px] text-[var(--color-text-muted)]">{formatDate(v.scheduledDate)}</span>
                          <VisitStatusBadge status={v.status} />
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Recent completed */}
              {recentVisits.length > 0 && (
                <div>
                  <p className="mb-1.5 text-xs font-medium text-[var(--color-text-muted)]">Recent Completed</p>
                  <div className="space-y-1">
                    {recentVisits.map(v => {
                      const building = getBuildingById(v.buildingId);
                      return (
                        <div key={v.id} className="flex items-center gap-2 rounded-lg bg-white/[0.02] px-2.5 py-1.5">
                          <TradeBadge trade={v.trade} size="sm" showIcon={false} />
                          <span className="flex-1 truncate text-xs text-[var(--color-text-muted)]">{building?.name}</span>
                          <span className="text-[11px] text-[var(--color-text-muted)]">{formatDate(v.scheduledDate)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
