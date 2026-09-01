// shadcn: Progress, Badge, Card — Inspection Checklist: trade-specific asset list
// Screen 3 (Tech) — Inspection Checklist: tappable assets, trade-specific checks, progress bar
import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getVisitById, getBuildingById, assets, getResultsByVisit } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { AssetTag } from '@/components/shared/AssetTag';
import { ArrowLeft, Circle, CheckCircle2, XCircle, ChevronRight } from 'lucide-react';

export default async function ChecklistPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const visit = getVisitById(id);
  if (!visit) notFound();

  const building = getBuildingById(visit.buildingId);
  const visitAssets = assets.filter(a => visit.assetIds.includes(a.id));
  const results = getResultsByVisit(id);
  const inspectedCount = results.length;
  const total = visitAssets.length;
  const pct = total > 0 ? Math.round((inspectedCount / total) * 100) : 0;

  return (
    <div className="px-4 py-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href={`/tech/jobs/${id}`} className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--color-border)] bg-white/5 text-[var(--color-text-muted)]">
          <ArrowLeft className="size-5" />
        </Link>
        <div>
          <h1 className="font-bold text-[var(--color-text-primary)]">{building?.name}</h1>
          <TradeBadge trade={visit.trade} size="sm" />
        </div>
      </div>

      {/* Progress */}
      <GlassCard padding="sm" className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-[var(--color-text-muted)]">Progress</span>
          <span className="font-medium text-[var(--color-text-primary)]">{inspectedCount} of {total} inspected</span>
        </div>
        <div className="h-2 rounded-full bg-white/10">
          <div className="h-full rounded-full bg-[var(--color-accent-primary)] transition-all" style={{ width: `${pct}%` }} />
        </div>
      </GlassCard>

      {/* Asset list — trade-specific items (HVAC shows AHU/FCU, fire shows extinguisher/detector, etc.) */}
      <div className="space-y-2">
        {visitAssets.map(asset => {
          const result = results.find(r => r.assetId === asset.id);
          const isLocked = result?.synced;

          return (
            <Link
              key={asset.id}
              href={isLocked ? '#' : `/tech/jobs/${id}/asset/${asset.id}`}
              className={`block ${isLocked ? 'pointer-events-none opacity-70' : ''}`}
            >
              <GlassCard padding="md" className={`flex items-center gap-4 ${!isLocked ? 'hover:bg-white/[0.06] active:scale-[0.98] cursor-pointer' : ''} transition-all`}>
                {/* Result icon */}
                <div className="shrink-0">
                  {result ? (
                    result.pass
                      ? <CheckCircle2 className="size-7 text-[var(--color-status-ok)]" />
                      : <XCircle className="size-7 text-[var(--color-status-critical)]" />
                  ) : (
                    <Circle className="size-7 text-[var(--color-text-subtle)]" />
                  )}
                </div>

                {/* Asset info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <AssetTag tag={asset.tag} />
                    {isLocked && (
                      <span className="text-[10px] text-[var(--color-text-subtle)] rounded-full bg-white/5 px-1.5 py-0.5">Locked</span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-[var(--color-text-primary)]">{asset.type}</p>
                  {result && (
                    <p className={`text-xs mt-0.5 ${result.pass ? 'text-[var(--color-status-ok)]' : 'text-[var(--color-status-critical)]'}`}>
                      {result.pass ? '✓ Pass' : '✗ Fail'} {!result.synced && '· queued'}
                    </p>
                  )}
                </div>

                {!result && <ChevronRight className="size-5 text-[var(--color-text-muted)] shrink-0" />}
              </GlassCard>
            </Link>
          );
        })}
      </div>

      {inspectedCount === total && total > 0 && (
        <Link
          href="/tech/sync"
          className="flex items-center justify-center gap-2 w-full rounded-2xl bg-[var(--color-status-ok)] py-4 text-base font-semibold text-white hover:opacity-90 active:scale-[0.98] transition-all"
        >
          <CheckCircle2 className="size-5" /> All done — Review & Sync
        </Link>
      )}
    </div>
  );
}
