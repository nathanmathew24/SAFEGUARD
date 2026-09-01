'use client';
// Custom composition: SyncIndicator + Badge + Progress — offline-first sync queue
// Screen 5 (Tech) — Sync/Queue State: queued vs synced results, offline-first UX
import { useState } from 'react';
import { assetResults, assets, visits, getVisitById, getAssetById } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { SyncIndicator } from '@/components/shared/SyncIndicator';
import { AssetTag } from '@/components/shared/AssetTag';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { formatDateTime } from '@/lib/utils';
import { CloudOff, CheckCircle2, RefreshCw, Lock, Wifi } from 'lucide-react';

const CURRENT_TECH = 'tech-001';

export default function SyncPage() {
  const techResults = assetResults.filter(r => r.technicianId === CURRENT_TECH);
  const [queued, setQueued] = useState(techResults.filter(r => !r.synced));
  const [synced, setSynced] = useState(techResults.filter(r => r.synced));
  const [syncing, setSyncing] = useState(false);
  const [done, setDone] = useState(false);

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => {
      setSynced(prev => [...prev, ...queued]);
      setQueued([]);
      setSyncing(false);
      setDone(true);
    }, 1800);
  };

  return (
    <div className="px-4 py-5 space-y-5">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text-primary)]">Sync</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Results save locally and upload when connected.</p>
      </div>

      {/* Large sync indicator */}
      <SyncIndicator queued={queued.length} synced={synced.length} syncing={syncing} size="lg" />

      {/* Offline note */}
      <GlassCard padding="sm" className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
        <Wifi className="size-4 text-[var(--color-status-ok)] shrink-0" />
        Results are saved locally with no network and will upload automatically when connected.
      </GlassCard>

      {/* Queued */}
      {queued.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold text-[var(--color-status-warning)] uppercase tracking-widest">
            Queued — not yet synced
          </p>
          <div className="space-y-2">
            {queued.map(result => {
              const asset = getAssetById(result.assetId);
              const visit = getVisitById(result.visitId);
              return (
                <GlassCard key={result.id} padding="sm" className="flex items-center gap-3 border-[var(--color-status-warning)]/20">
                  <span className="size-2 rounded-full bg-[var(--color-status-warning)] animate-pulse shrink-0" />
                  {asset && <AssetTag tag={asset.tag} />}
                  {asset && <TradeBadge trade={asset.trade} size="sm" showIcon={false} />}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-[var(--color-text-primary)] truncate">{asset?.type}</p>
                    <p className="text-[11px] text-[var(--color-text-muted)]">{formatDateTime(result.timestamp)}</p>
                  </div>
                  <span className={`text-xs font-medium ${result.pass ? 'text-[var(--color-status-ok)]' : 'text-[var(--color-status-critical)]'}`}>
                    {result.pass ? 'Pass' : 'Fail'}
                  </span>
                </GlassCard>
              );
            })}
          </div>
        </div>
      )}

      {/* Sync Now button */}
      {queued.length > 0 && (
        <button
          onClick={handleSync}
          disabled={syncing}
          className="flex items-center justify-center gap-2 w-full rounded-2xl bg-[var(--color-accent-primary)] py-4 text-base font-semibold text-white hover:bg-[var(--color-accent-primary-hover)] disabled:opacity-60 active:scale-[0.98] transition-all"
        >
          <RefreshCw className={`size-5 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing…' : 'Sync Now'}
        </button>
      )}

      {done && queued.length === 0 && (
        <div className="flex items-center gap-2 rounded-xl bg-[var(--color-status-ok-bg)] p-4 text-sm text-[var(--color-status-ok)]">
          <CheckCircle2 className="size-5 shrink-0" /> All results synced successfully.
        </div>
      )}

      {/* Synced & locked */}
      {synced.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">
            Synced & Locked
          </p>
          <div className="space-y-2">
            {synced.map(result => {
              const asset = getAssetById(result.assetId);
              return (
                <GlassCard key={result.id} padding="sm" className="flex items-center gap-3 opacity-70">
                  <CheckCircle2 className="size-4 text-[var(--color-status-ok)] shrink-0" />
                  {asset && <AssetTag tag={asset.tag} />}
                  {asset && <TradeBadge trade={asset.trade} size="sm" showIcon={false} />}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-[var(--color-text-muted)] truncate">{asset?.type}</p>
                    <p className="text-[11px] text-[var(--color-text-subtle)]">{formatDateTime(result.timestamp)}</p>
                  </div>
                  <Lock className="size-3.5 text-[var(--color-text-subtle)] shrink-0" />
                </GlassCard>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
