// shadcn: Card, Badge, Button — Job Detail: building info, trade, checklist preview, start button
// Screen 2 (Tech) — Job Detail: view before starting inspection
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getVisitById, getBuildingById, getTechnicianById, assets, getResultsByVisit } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { VisitStatusBadge } from '@/components/shared/VisitStatusBadge';
import { AssetTag } from '@/components/shared/AssetTag';
import { getAssetStatusColor } from '@/lib/utils';
import { ArrowLeft, MapPin, Clock, CheckCircle2, Circle, XCircle, ChevronRight } from 'lucide-react';

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const visit = getVisitById(id);
  if (!visit) notFound();

  const building = getBuildingById(visit.buildingId);
  const tech = getTechnicianById(visit.technicianId);
  const visitAssets = assets.filter(a => visit.assetIds.includes(a.id));
  const results = getResultsByVisit(id);

  const isCompleted = visit.status === 'completed';
  const passCount = results.filter(r => r.pass).length;
  const failCount = results.filter(r => !r.pass).length;

  return (
    <div className="px-4 py-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href="/tech/jobs" className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--color-border)] bg-white/5 text-[var(--color-text-muted)]">
          <ArrowLeft className="size-5" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="font-bold text-[var(--color-text-primary)] text-lg leading-tight truncate">{building?.name}</h1>
          <VisitStatusBadge status={visit.status} />
        </div>
      </div>

      {/* Building info */}
      <GlassCard padding="md" className="space-y-3">
        <div className="flex items-start gap-2 text-sm text-[var(--color-text-muted)]">
          <MapPin className="size-4 mt-0.5 shrink-0" />
          <span>{building?.address}</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-1.5 text-[var(--color-text-muted)]">
            <Clock className="size-4" />
            <span>{visit.scheduledTime}</span>
          </div>
          <TradeBadge trade={visit.trade} />
        </div>
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          <div className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-400">{tech?.initials}</div>
          <span>{tech?.name}</span>
          <span className="text-[var(--color-text-subtle)]">· locked read-only</span>
        </div>
      </GlassCard>

      {/* Completed summary */}
      {isCompleted && (
        <GlassCard padding="md">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-3">Inspection Summary</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col items-center rounded-xl bg-[var(--color-status-ok-bg)] py-4">
              <CheckCircle2 className="size-7 text-[var(--color-status-ok)] mb-1" />
              <span className="text-2xl font-bold text-[var(--color-status-ok)]">{passCount}</span>
              <span className="text-xs text-[var(--color-text-muted)]">Passed</span>
            </div>
            <div className="flex flex-col items-center rounded-xl bg-[var(--color-status-critical-bg)] py-4">
              <XCircle className="size-7 text-[var(--color-status-critical)] mb-1" />
              <span className="text-2xl font-bold text-[var(--color-status-critical)]">{failCount}</span>
              <span className="text-xs text-[var(--color-text-muted)]">Failed</span>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Checklist preview */}
      <GlassCard padding="md">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Assets to Inspect</h3>
          <span className="text-xs text-[var(--color-text-muted)]">{visitAssets.length} item{visitAssets.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="space-y-2">
          {visitAssets.map(asset => {
            const result = results.find(r => r.assetId === asset.id);
            const sc = getAssetStatusColor(asset.status);
            return (
              <div key={asset.id} className="flex items-center gap-3 rounded-xl bg-white/[0.02] px-3 py-3">
                <div className="shrink-0">
                  {result ? (
                    result.pass
                      ? <CheckCircle2 className="size-5 text-[var(--color-status-ok)]" />
                      : <XCircle className="size-5 text-[var(--color-status-critical)]" />
                  ) : (
                    <Circle className="size-5 text-[var(--color-text-subtle)]" />
                  )}
                </div>
                <AssetTag tag={asset.tag} />
                <span className="flex-1 text-sm text-[var(--color-text-primary)]">{asset.type}</span>
                {result && (
                  <span className={`text-xs font-medium ${result.pass ? 'text-[var(--color-status-ok)]' : 'text-[var(--color-status-critical)]'}`}>
                    {result.pass ? 'Pass' : 'Fail'}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </GlassCard>

      {/* Primary action */}
      {!isCompleted && (
        <Link
          href={`/tech/jobs/${id}/checklist`}
          className="flex items-center justify-center gap-2 w-full rounded-2xl bg-[var(--color-accent-primary)] py-4 text-base font-semibold text-white hover:bg-[var(--color-accent-primary-hover)] active:scale-[0.98] transition-all"
        >
          Start Inspection <ChevronRight className="size-5" />
        </Link>
      )}
    </div>
  );
}
