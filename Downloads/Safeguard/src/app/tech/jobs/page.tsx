// shadcn: Card, Badge — Today's Jobs: unified list for current technician
// Screen 1 (Tech) — Today's Jobs: building, address, time, trade badge, status
// Mobile-first single column, large tap targets
import Link from 'next/link';
import { visits, getBuildingById } from '@/lib/mockData';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { VisitStatusBadge } from '@/components/shared/VisitStatusBadge';
import { GlassCard } from '@/components/shared/GlassCard';
import { Clock, ChevronRight, MapPin, CalendarCheck } from 'lucide-react';

const TODAY = '2026-09-01';
const CURRENT_TECH = 'tech-001'; // Ahmed Al Mansoori — fire+hvac

export default function TechJobsPage() {
  // All today's jobs for this technician — unified list, not split by trade
  const todaysJobs = visits
    .filter(v => v.technicianId === CURRENT_TECH && v.scheduledDate === TODAY)
    .sort((a, b) => a.scheduledTime.localeCompare(b.scheduledTime));

  const completedCount = todaysJobs.filter(v => v.status === 'completed').length;
  const total = todaysJobs.length;

  return (
    <div className="px-4 py-5 space-y-4">
      {/* Greeting */}
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text-primary)]">Good morning, Ahmed</h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          {new Date(TODAY).toLocaleDateString('en-AE', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
        </p>
      </div>

      {/* Progress bar */}
      <GlassCard padding="sm" className="flex items-center gap-3">
        <CalendarCheck className="size-4 text-[var(--color-accent-primary)] shrink-0" />
        <div className="flex-1">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-[var(--color-text-muted)]">Today's progress</span>
            <span className="font-medium text-[var(--color-text-primary)]">{completedCount}/{total} done</span>
          </div>
          <div className="h-1.5 rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-[var(--color-accent-primary)] transition-all"
              style={{ width: total > 0 ? `${(completedCount / total) * 100}%` : '0%' }}
            />
          </div>
        </div>
      </GlassCard>

      {/* Job list */}
      {todaysJobs.length === 0 ? (
        <div className="py-16 text-center">
          <CalendarCheck className="mx-auto size-10 text-[var(--color-text-subtle)] mb-3" />
          <p className="text-sm text-[var(--color-text-muted)]">No jobs scheduled for today.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {todaysJobs.map(job => {
            const building = getBuildingById(job.buildingId);
            return (
              <Link key={job.id} href={`/tech/jobs/${job.id}`}>
                <GlassCard padding="md" className="flex items-stretch gap-3 hover:bg-white/[0.06] transition-colors cursor-pointer active:scale-[0.98]">
                  {/* Time column */}
                  <div className="flex flex-col items-center justify-center w-14 shrink-0 rounded-xl bg-white/5 py-2">
                    <Clock className="size-4 text-[var(--color-text-muted)] mb-1" />
                    <span className="text-xs font-bold text-[var(--color-text-primary)]">{job.scheduledTime}</span>
                  </div>
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-[var(--color-text-primary)] text-base leading-tight">{building?.name}</p>
                    <div className="flex items-center gap-1 mt-0.5 text-xs text-[var(--color-text-muted)]">
                      <MapPin className="size-3 shrink-0" />
                      <span className="truncate">{building?.address}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                      <TradeBadge trade={job.trade} size="sm" />
                      <VisitStatusBadge status={job.status} />
                    </div>
                  </div>
                  <div className="flex items-center">
                    <ChevronRight className="size-5 text-[var(--color-text-muted)]" />
                  </div>
                </GlassCard>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
