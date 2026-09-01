'use client';
// shadcn: Button, Badge, Card — Asset Result + Evidence capture
// Screen 4 (Tech) — Asset Result: pass/fail toggle, photo capture, auto metadata, sync lock
import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { assets, getVisitById, getResultsByVisit } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { AssetTag } from '@/components/shared/AssetTag';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { ArrowLeft, CheckCircle2, XCircle, Camera, Lock, User, Clock, Smartphone, Save } from 'lucide-react';

const CURRENT_TECH_NAME = 'Ahmed Al Mansoori';
const DEVICE_META = 'Samsung Galaxy A54 · Android 14';

export default function AssetResultPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const assetId = params.assetId as string;

  const visit = getVisitById(id);
  const asset = assets.find(a => a.id === assetId);

  const existingResults = getResultsByVisit(id);
  const existingResult = existingResults.find(r => r.assetId === assetId);
  const isLocked = existingResult?.synced ?? false;

  const [pass, setPass] = useState<boolean | null>(existingResult ? existingResult.pass : null);
  const [hasPhoto, setHasPhoto] = useState(existingResult?.photo ? true : false);
  const [saved, setSaved] = useState(!!existingResult);
  const [timestamp] = useState(new Date().toISOString());

  if (!asset || !visit) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <p className="text-[var(--color-text-muted)]">Asset not found.</p>
      </div>
    );
  }

  const requiresPhoto = pass === false;
  const canSave = pass !== null && (!requiresPhoto || hasPhoto) && !isLocked;

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => router.push(`/tech/jobs/${id}/checklist`), 800);
  };

  return (
    <div className="px-4 py-5 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Link href={`/tech/jobs/${id}/checklist`} className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--color-border)] bg-white/5 text-[var(--color-text-muted)]">
          <ArrowLeft className="size-5" />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <AssetTag tag={asset.tag} />
            <TradeBadge trade={asset.trade} size="sm" />
            {isLocked && (
              <span className="flex items-center gap-1 rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-[var(--color-text-muted)]">
                <Lock className="size-3" /> Synced & Locked
              </span>
            )}
          </div>
          <p className="mt-1 text-base font-bold text-[var(--color-text-primary)]">{asset.type}</p>
        </div>
      </div>

      {/* Auto-captured metadata (read-only — never manually entered) */}
      <GlassCard padding="md" className="space-y-2">
        <p className="text-xs font-medium text-[var(--color-text-muted)] mb-1">Auto-captured · Read only</p>
        {[
          { icon: User, label: 'Technician', value: CURRENT_TECH_NAME },
          { icon: Clock, label: 'Timestamp', value: new Date(timestamp).toLocaleString('en-AE') },
          { icon: Smartphone, label: 'Device', value: DEVICE_META },
        ].map(({ icon: Icon, label, value }) => (
          <div key={label} className="flex items-center gap-2 text-xs">
            <Icon className="size-3.5 text-[var(--color-text-subtle)] shrink-0" />
            <span className="text-[var(--color-text-muted)] w-20 shrink-0">{label}</span>
            <span className="text-[var(--color-text-primary)]">{value}</span>
          </div>
        ))}
      </GlassCard>

      {/* Pass / Fail toggle — large tap targets */}
      <div className="grid grid-cols-2 gap-3">
        <button
          disabled={isLocked}
          onClick={() => { setPass(true); setHasPhoto(false); }}
          className={`flex flex-col items-center gap-2 rounded-2xl py-6 text-sm font-bold transition-all active:scale-95 disabled:opacity-50 ${pass === true ? 'bg-[var(--color-status-ok)] text-white shadow-lg shadow-green-900/30' : 'border border-[var(--color-status-ok)]/30 bg-[var(--color-status-ok-bg)] text-[var(--color-status-ok)] hover:bg-[rgba(16,185,129,0.2)]'}`}
        >
          <CheckCircle2 className="size-8" />
          PASS
        </button>
        <button
          disabled={isLocked}
          onClick={() => setPass(false)}
          className={`flex flex-col items-center gap-2 rounded-2xl py-6 text-sm font-bold transition-all active:scale-95 disabled:opacity-50 ${pass === false ? 'bg-[var(--color-status-critical)] text-white shadow-lg shadow-red-900/30' : 'border border-[var(--color-status-critical)]/30 bg-[var(--color-status-critical-bg)] text-[var(--color-status-critical)] hover:bg-[rgba(239,68,68,0.2)]'}`}
        >
          <XCircle className="size-8" />
          FAIL
        </button>
      </div>

      {/* Photo evidence — required on fail */}
      {pass === false && (
        <GlassCard padding="md" className="space-y-3">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-[var(--color-text-primary)]">Photo Evidence</p>
            <span className="text-[10px] text-[var(--color-status-critical)]">Required on fail</span>
          </div>
          {hasPhoto ? (
            <div className="flex items-center gap-2 rounded-xl bg-[var(--color-status-ok-bg)] p-3">
              <CheckCircle2 className="size-4 text-[var(--color-status-ok)]" />
              <span className="text-xs text-[var(--color-status-ok)]">Photo captured</span>
            </div>
          ) : (
            <button
              disabled={isLocked}
              onClick={() => setHasPhoto(true)}
              className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-[var(--color-border-strong)] bg-white/5 py-6 text-sm text-[var(--color-text-muted)] hover:bg-white/8 hover:text-[var(--color-text-primary)] transition-colors disabled:opacity-50"
            >
              <Camera className="size-5" /> Capture Photo
            </button>
          )}
        </GlassCard>
      )}

      {/* Save button */}
      {!isLocked && (
        <button
          disabled={!canSave || saved}
          onClick={handleSave}
          className={`flex items-center justify-center gap-2 w-full rounded-2xl py-4 text-base font-semibold transition-all active:scale-[0.98] disabled:opacity-40 ${saved ? 'bg-[var(--color-status-ok)] text-white' : 'bg-[var(--color-accent-primary)] text-white hover:bg-[var(--color-accent-primary-hover)]'}`}
        >
          {saved ? <><CheckCircle2 className="size-5" /> Saved & Queued</> : <><Save className="size-5" /> Save Result</>}
        </button>
      )}

      {isLocked && (
        <div className="flex items-center gap-2 rounded-xl bg-white/5 p-4 text-xs text-[var(--color-text-muted)]">
          <Lock className="size-4 shrink-0" />
          This result has been synced and is locked. No further edits are possible.
        </div>
      )}
    </div>
  );
}
