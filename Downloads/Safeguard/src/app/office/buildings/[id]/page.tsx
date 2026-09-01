// shadcn: Tabs, TabsList, TabsTrigger, TabsContent, Card — Building detail with 4 tabs
// Screen 2 detail — Building detail: Overview | Assets | Visit History | Issues
import { notFound } from 'next/navigation';
import Link from 'next/link';
import {
  getBuildingById, getAssetsByBuilding, getVisitsByTechnician,
  getIssuesByBuilding, getTechnicianById, visits, assetResults,
} from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { AssetTag } from '@/components/shared/AssetTag';
import { VisitStatusBadge } from '@/components/shared/VisitStatusBadge';
import { TRADES } from '@/lib/mockData';
import { formatDate, getStatusColor, getAssetStatusColor } from '@/lib/utils';
import { ArrowLeft, MapPin, Phone, Mail } from 'lucide-react';

export default async function BuildingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const building = getBuildingById(id);
  if (!building) notFound();

  const buildingAssets = getAssetsByBuilding(id);
  const buildingIssues = getIssuesByBuilding(id);
  const buildingVisits = visits.filter(v => v.buildingId === id).sort(
    (a, b) => new Date(b.scheduledDate).getTime() - new Date(a.scheduledDate).getTime()
  );
  const techs = building.assignedTechnicianIds.map(tid => getTechnicianById(tid)).filter(Boolean);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <Link href="/office/buildings" className="flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--color-border)] bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors">
            <ArrowLeft className="size-4" />
          </Link>
          <div>
            <h1 className="text-lg font-bold text-[var(--color-text-primary)]">{building.name}</h1>
            <div className="flex items-center gap-1.5 mt-0.5 text-xs text-[var(--color-text-muted)]">
              <MapPin className="size-3" /> {building.address}
            </div>
          </div>
        </div>
        <StatusBadge status={building.health} />
      </div>

      {/* Tab layout — implemented as client-free anchor tabs for simplicity */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Overview */}
        <GlassCard padding="md" className="lg:col-span-1 flex flex-col gap-4">
          <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Building Info</h3>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Emirate</span><span className="text-[var(--color-text-primary)]">{building.emirate}</span></div>
            <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Trades</span><div className="flex gap-1">{building.trades.map(t => <TradeBadge key={t} trade={t} size="sm" />)}</div></div>
            <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Assets</span><span className="text-[var(--color-text-primary)]">{building.assetCount}</span></div>
            <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Next Inspection</span><span className="text-[var(--color-text-primary)]">{formatDate(building.nextInspection)}</span></div>
            <div className="flex justify-between"><span className="text-[var(--color-text-muted)]">Last Inspection</span><span className="text-[var(--color-text-primary)]">{formatDate(building.lastInspection)}</span></div>
          </div>

          {/* Per-trade health */}
          <div>
            <p className="mb-2 text-xs font-medium text-[var(--color-text-muted)]">Trade Health</p>
            <div className="space-y-2">
              {TRADES.map(trade => {
                const health = building.tradeHealth[trade.id];
                if (!building.trades.includes(trade.id)) return null;
                const sc = health ? getStatusColor(health) : null;
                return (
                  <div key={trade.id} className="flex items-center justify-between">
                    <TradeBadge trade={trade.id} size="sm" />
                    {sc ? <StatusBadge status={health!} size="sm" /> : <span className="text-[11px] text-[var(--color-text-subtle)]">Not in scope</span>}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Owner contact */}
          <div>
            <p className="mb-2 text-xs font-medium text-[var(--color-text-muted)]">Owner Contact</p>
            <div className="space-y-1 text-xs">
              <p className="font-medium text-[var(--color-text-primary)]">{building.ownerContact.name}</p>
              <div className="flex items-center gap-1.5 text-[var(--color-text-muted)]"><Phone className="size-3" />{building.ownerContact.phone}</div>
              <div className="flex items-center gap-1.5 text-[var(--color-text-muted)]"><Mail className="size-3" />{building.ownerContact.email}</div>
            </div>
          </div>
        </GlassCard>

        <div className="lg:col-span-2 space-y-4">
          {/* Assets */}
          <GlassCard padding="md">
            <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">Assets</h3>
            <div className="space-y-1.5">
              {buildingAssets.map(asset => {
                const asc = getAssetStatusColor(asset.status);
                return (
                  <div key={asset.id} className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2">
                    <AssetTag tag={asset.tag} />
                    <TradeBadge trade={asset.trade} size="sm" showIcon={false} />
                    <span className="flex-1 text-xs text-[var(--color-text-primary)]">{asset.type}</span>
                    <span className={`text-xs font-medium ${asc.text}`}>{asc.label}</span>
                    <span className="text-[11px] text-[var(--color-text-muted)]">{formatDate(asset.lastChecked)}</span>
                  </div>
                );
              })}
            </div>
          </GlassCard>

          {/* Visit History */}
          <GlassCard padding="md">
            <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">Visit History</h3>
            <div className="space-y-1.5">
              {buildingVisits.map(visit => {
                const tech = getTechnicianById(visit.technicianId);
                return (
                  <div key={visit.id} className="flex items-center gap-3 rounded-lg bg-white/[0.02] px-3 py-2">
                    <TradeBadge trade={visit.trade} size="sm" />
                    <span className="flex-1 text-xs text-[var(--color-text-muted)]">{formatDate(visit.scheduledDate)} · {visit.scheduledTime}</span>
                    {tech && <span className="text-[11px] text-[var(--color-text-muted)]">{tech.name}</span>}
                    <VisitStatusBadge status={visit.status} />
                  </div>
                );
              })}
            </div>
          </GlassCard>

          {/* Open Issues */}
          {buildingIssues.length > 0 && (
            <GlassCard padding="md">
              <h3 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">Open Issues</h3>
              <div className="space-y-1.5">
                {buildingIssues.map(issue => {
                  const asset = buildingAssets.find(a => a.id === issue.assetId);
                  return (
                    <div key={issue.id} className="flex items-start gap-3 rounded-lg bg-white/[0.02] px-3 py-2">
                      {asset && <AssetTag tag={asset.tag} />}
                      <TradeBadge trade={issue.trade} size="sm" />
                      <p className="flex-1 text-xs text-[var(--color-text-muted)] line-clamp-1">{issue.description}</p>
                      <span className={`text-xs font-medium ${issue.priority === 'high' ? 'text-[var(--color-status-critical)]' : issue.priority === 'medium' ? 'text-[var(--color-status-warning)]' : 'text-[var(--color-status-ok)]'}`}>
                        {issue.priority}
                      </span>
                    </div>
                  );
                })}
              </div>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
