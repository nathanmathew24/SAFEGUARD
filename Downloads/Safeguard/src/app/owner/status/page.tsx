// shadcn: Card, Badge, Progress — Building Status: per-trade health, inspection dates, asset summary
// Screen 1 (Owner) — Building Status: clear compliance state per trade, next/last inspection, asset health
// Cross-portal consistency: EX-014 fail → Al Quoz fire = critical
import { buildings, assets, TRADES } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { formatDate, getDaysUntil, getStatusColor, getTradeColor } from '@/lib/utils';
import { Building2, CalendarCheck, CalendarClock, CheckCircle2, AlertTriangle } from 'lucide-react';

// Owner sees Al Quoz Industrial Centre (building with fire+hvac+elv — the cross-portal anchor)
const OWNER_BUILDING_ID = 'bld-001';

export default function OwnerStatusPage() {
  const building = buildings.find(b => b.id === OWNER_BUILDING_ID)!;
  const buildingAssets = assets.filter(a => a.buildingId === OWNER_BUILDING_ID);
  const passCount = buildingAssets.filter(a => a.status === 'pass').length;
  const total = buildingAssets.length;
  const pct = Math.round((passCount / total) * 100);
  const daysUntil = getDaysUntil(building.nextInspection);
  const overallStatus = building.health;
  const sc = getStatusColor(overallStatus);

  return (
    <div className="space-y-5">
      {/* Hero card — most important: overall compliance state */}
      <GlassCard padding="lg" className={`border ${sc.border}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${sc.bg} shrink-0`}>
              {overallStatus === 'ok'
                ? <CheckCircle2 className={`size-6 ${sc.text}`} />
                : <AlertTriangle className={`size-6 ${sc.text}`} />
              }
            </div>
            <div>
              <h1 className="text-lg font-bold text-[var(--color-text-primary)]">{building.name}</h1>
              <p className="text-sm text-[var(--color-text-muted)]">{building.emirate} · AMC Active</p>
            </div>
          </div>
          <StatusBadge status={overallStatus} />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-white/[0.03] p-3 space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
              <CalendarClock className="size-3.5" /> Last Inspection
            </div>
            <p className="font-semibold text-[var(--color-text-primary)]">{formatDate(building.lastInspection)}</p>
          </div>
          <div className="rounded-xl bg-white/[0.03] p-3 space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
              <CalendarCheck className="size-3.5" /> Next Inspection
            </div>
            <p className="font-semibold text-[var(--color-text-primary)]">
              {formatDate(building.nextInspection)}
              <span className={`ml-1.5 text-xs ${daysUntil <= 7 ? 'text-[var(--color-status-warning)]' : 'text-[var(--color-text-muted)]'}`}>
                ({daysUntil > 0 ? `in ${daysUntil}d` : 'overdue'})
              </span>
            </p>
          </div>
        </div>
      </GlassCard>

      {/* Per-trade health breakdown */}
      <div>
        <h2 className="mb-3 text-sm font-semibold text-[var(--color-text-primary)]">Compliance by Trade</h2>
        <div className="space-y-3">
          {TRADES.map(trade => {
            const inScope = building.trades.includes(trade.id);
            const tradeHealth = building.tradeHealth[trade.id];
            const sc = tradeHealth ? getStatusColor(tradeHealth) : null;
            const tc = getTradeColor(trade.id);
            const tradeAssets = buildingAssets.filter(a => a.trade === trade.id);
            const tradePass = tradeAssets.filter(a => a.status === 'pass').length;

            return (
              <GlassCard key={trade.id} padding="md" className={`space-y-3 ${!inScope ? 'opacity-50' : ''}`}>
                <div className="flex items-center justify-between">
                  <TradeBadge trade={trade.id} />
                  {!inScope ? (
                    <span className="text-xs text-[var(--color-text-subtle)]">Not in scope</span>
                  ) : tradeHealth ? (
                    <StatusBadge status={tradeHealth} />
                  ) : null}
                </div>
                {inScope && tradeAssets.length > 0 && (
                  <>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-[var(--color-text-muted)]">Asset health</span>
                      <span className="font-medium text-[var(--color-text-primary)]">{tradePass}/{tradeAssets.length} passing</span>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-white/10">
                      <div
                        className={`h-full rounded-full transition-all ${sc?.dot ?? 'bg-white/20'}`}
                        style={{ width: `${tradeAssets.length > 0 ? (tradePass / tradeAssets.length) * 100 : 0}%` }}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-[var(--color-text-muted)]">
                      <div>Last: {formatDate(Math.max(...tradeAssets.map(a => new Date(a.lastChecked).getTime())).toString() !== 'NaN' ? tradeAssets.sort((a,b) => new Date(b.lastChecked).getTime() - new Date(a.lastChecked).getTime())[0].lastChecked : building.lastInspection)}</div>
                      <div className="text-right">Next: {formatDate(Math.min(...tradeAssets.map(a => new Date(a.nextDue).getTime())).toString() !== 'NaN' ? tradeAssets.sort((a,b) => new Date(a.nextDue).getTime() - new Date(b.nextDue).getTime())[0].nextDue : building.nextInspection)}</div>
                    </div>
                  </>
                )}
              </GlassCard>
            );
          })}
        </div>
      </div>

      {/* At-a-glance asset summary */}
      <GlassCard padding="md" className="space-y-3">
        <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Asset Health Overview</h2>
        <div className="flex items-center justify-between text-sm">
          <span className="text-[var(--color-text-muted)]">{passCount} of {total} assets OK</span>
          <span className={`font-bold ${pct === 100 ? 'text-[var(--color-status-ok)]' : pct >= 70 ? 'text-[var(--color-status-warning)]' : 'text-[var(--color-status-critical)]'}`}>{pct}%</span>
        </div>
        <div className="h-2.5 rounded-full bg-white/10">
          <div
            className={`h-full rounded-full transition-all ${pct === 100 ? 'bg-[var(--color-status-ok)]' : pct >= 70 ? 'bg-[var(--color-status-warning)]' : 'bg-[var(--color-status-critical)]'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-xs text-[var(--color-text-muted)]">
          Serviced by Emirates Safety Systems · {building.emirate} AMC
        </p>
      </GlassCard>
    </div>
  );
}
