// shadcn: Card, CardHeader, CardTitle, CardContent, Progress, Badge, Separator, Table
// Screen 1 — Overview: command centre with KPI cards, decision panel, event feed, building health grid
import { buildings, visits, issues, assets, technicians, assetResults, getTechnicianById, getBuildingById } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { VisitStatusBadge } from '@/components/shared/VisitStatusBadge';
import { AssetTag } from '@/components/shared/AssetTag';
import { formatDate, formatDateTime, getStatusColor } from '@/lib/utils';
import {
  Building2, AlertTriangle, CalendarCheck, Activity,
  TrendingUp, Clock, CheckCircle2, XCircle, ArrowRight,
} from 'lucide-react';
import Link from 'next/link';

const TODAY = '2026-09-01';

export default function OverviewPage() {
  const totalAssets = assets.length;
  const passAssets = assets.filter(a => a.status === 'pass').length;
  const healthPct = Math.round((passAssets / totalAssets) * 100);
  const inspectionsThisWeek = visits.filter(v =>
    v.scheduledDate >= TODAY && v.scheduledDate <= '2026-09-07'
  ).length;
  const openIssues = issues.filter(i => i.status !== 'resolved').length;
  const overdueVisits = visits.filter(v => v.status === 'overdue');
  const todaysVisits = visits.filter(v => v.scheduledDate === TODAY);

  // Recent events feed — last 5 completed/in-progress activities
  const recentEvents = [
    { id: 'e1', text: 'EX-014 fire extinguisher failed inspection', building: 'Al Quoz Industrial Centre', trade: 'fire' as const, time: '2026-07-15T10:15:00Z', type: 'fail' },
    { id: 'e2', text: 'HVAC inspection completed — AHU-03 pass', building: 'Al Quoz Industrial Centre', trade: 'hvac' as const, time: '2026-09-01T09:35:00Z', type: 'pass' },
    { id: 'e3', text: 'Fire & ELV renewal pack generated', building: 'Sharjah Expo Business Centre', trade: 'fire' as const, time: '2026-08-12T14:00:00Z', type: 'info' },
    { id: 'e4', text: 'AHU-09 service certificate expired', building: 'Marina Gate Residences', trade: 'hvac' as const, time: '2026-08-02T08:00:00Z', type: 'warning' },
    { id: 'e5', text: 'Al Reem HVAC inspection completed', building: 'Al Reem Tower', trade: 'hvac' as const, time: '2026-08-20T10:45:00Z', type: 'pass' },
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());

  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <GlassCard padding="md" className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[var(--color-text-muted)]">Portfolio Health</span>
            <TrendingUp className="size-4 text-[var(--color-status-ok)]" />
          </div>
          <div>
            <p className="text-3xl font-bold text-[var(--color-text-primary)]">{healthPct}%</p>
            <p className="text-xs text-[var(--color-text-muted)]">{passAssets} of {totalAssets} assets passing</p>
          </div>
          <div className="h-1.5 w-full rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-[var(--color-status-ok)] transition-all"
              style={{ width: `${healthPct}%` }}
            />
          </div>
        </GlassCard>

        <GlassCard padding="md" className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[var(--color-text-muted)]">Buildings Monitored</span>
            <Building2 className="size-4 text-[var(--color-accent-primary)]" />
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)]">{buildings.length}</p>
          <p className="text-xs text-[var(--color-text-muted)]">3 emirates · Dubai, Sharjah, Abu Dhabi</p>
        </GlassCard>

        <GlassCard padding="md" className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[var(--color-text-muted)]">Inspections This Week</span>
            <CalendarCheck className="size-4 text-sky-400" />
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)]">{inspectionsThisWeek}</p>
          <p className="text-xs text-[var(--color-text-muted)]">{todaysVisits.length} scheduled today</p>
        </GlassCard>

        <GlassCard padding="md" className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-[var(--color-text-muted)]">Open Issues</span>
            <AlertTriangle className="size-4 text-[var(--color-status-warning)]" />
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)]">{openIssues}</p>
          <p className="text-xs text-[var(--color-text-muted)]">
            {issues.filter(i => i.priority === 'high' && i.status !== 'resolved').length} high priority
          </p>
        </GlassCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Requires a Decision */}
        <GlassCard padding="md" className="lg:col-span-1 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Requires a Decision</h3>
            <span className="rounded-full bg-[var(--color-status-critical-bg)] px-2 py-0.5 text-xs font-medium text-[var(--color-status-critical)]">
              {overdueVisits.length + issues.filter(i => i.priority === 'high' && i.status !== 'resolved').length} items
            </span>
          </div>
          <div className="space-y-2">
            {overdueVisits.map(v => {
              const building = getBuildingById(v.buildingId);
              return (
                <Link key={v.id} href="/office/schedule" className="flex items-start gap-3 rounded-lg bg-[var(--color-status-critical-bg)] p-2.5 hover:bg-[rgba(239,68,68,0.18)] transition-colors">
                  <Clock className="mt-0.5 size-4 shrink-0 text-[var(--color-status-critical)]" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-[var(--color-text-primary)]">Overdue Inspection</p>
                    <p className="truncate text-[11px] text-[var(--color-text-muted)]">{building?.name} · {v.scheduledDate}</p>
                  </div>
                  <TradeBadge trade={v.trade} size="sm" />
                </Link>
              );
            })}
            {issues.filter(i => i.priority === 'high' && i.status !== 'resolved').map(issue => {
              const asset = assets.find(a => a.id === issue.assetId);
              const building = getBuildingById(issue.buildingId);
              return (
                <Link key={issue.id} href="/office/issues" className="flex items-start gap-3 rounded-lg bg-[var(--color-status-warning-bg)] p-2.5 hover:bg-[rgba(245,158,11,0.18)] transition-colors">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0 text-[var(--color-status-warning)]" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-[var(--color-text-primary)] flex items-center gap-1.5">
                      {asset && <AssetTag tag={asset.tag} />}
                      <span className="truncate">{building?.name}</span>
                    </p>
                    <p className="truncate text-[11px] text-[var(--color-text-muted)]">{issue.description.substring(0, 60)}…</p>
                  </div>
                  <TradeBadge trade={issue.trade} size="sm" />
                </Link>
              );
            })}
          </div>
        </GlassCard>

        {/* Live Event Feed */}
        <GlassCard padding="md" className="lg:col-span-2 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Recent Activity</h3>
            <Activity className="size-4 text-[var(--color-text-muted)]" />
          </div>
          <div className="space-y-2">
            {recentEvents.map(event => (
              <div key={event.id} className="flex items-start gap-3 rounded-lg bg-white/[0.02] p-2.5">
                <div className="mt-0.5 shrink-0">
                  {event.type === 'fail' ? (
                    <XCircle className="size-4 text-[var(--color-status-critical)]" />
                  ) : event.type === 'pass' ? (
                    <CheckCircle2 className="size-4 text-[var(--color-status-ok)]" />
                  ) : event.type === 'warning' ? (
                    <AlertTriangle className="size-4 text-[var(--color-status-warning)]" />
                  ) : (
                    <Activity className="size-4 text-[var(--color-accent-primary)]" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-[var(--color-text-primary)]">{event.text}</p>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{event.building} · {formatDateTime(event.time)}</p>
                </div>
                <TradeBadge trade={event.trade} size="sm" showIcon={false} />
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Building Health Grid */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Building Health</h3>
          <Link href="/office/buildings" className="flex items-center gap-1 text-xs text-[var(--color-accent-primary)] hover:underline">
            View all <ArrowRight className="size-3" />
          </Link>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {buildings.map(building => (
            <Link key={building.id} href={`/office/buildings/${building.id}`}>
              <GlassCard padding="md" className="flex flex-col gap-3 hover:bg-white/[0.06] transition-colors cursor-pointer">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-[var(--color-text-primary)]">{building.name}</p>
                    <p className="text-[11px] text-[var(--color-text-muted)]">{building.emirate}</p>
                  </div>
                  <StatusBadge status={building.health} size="sm" />
                </div>
                {/* Per-trade health dots */}
                <div className="flex gap-2">
                  {building.trades.map(trade => {
                    const tradeHealth = building.tradeHealth[trade];
                    const sc = tradeHealth ? getStatusColor(tradeHealth) : null;
                    return (
                      <div key={trade} className="flex items-center gap-1">
                        <TradeBadge trade={trade} size="sm" />
                        {sc && <span className={`size-1.5 rounded-full ${sc.dot}`} />}
                      </div>
                    );
                  })}
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--color-text-muted)]">
                  <span>{building.assetCount} assets</span>
                  <span>Next: {formatDate(building.nextInspection)}</span>
                </div>
              </GlassCard>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
