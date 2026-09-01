'use client';
// shadcn: Table, Select, Input, Badge, Sheet — Assets master list
// Screen 3 — Assets: tagged assets across all trades with filters
import { useState } from 'react';
import { assets, buildings, TRADES, getBuildingById } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { AssetTag } from '@/components/shared/AssetTag';
import { formatDate, getAssetStatusColor } from '@/lib/utils';
import type { TradeType, AssetStatus } from '@/lib/types';
import { Search, Filter } from 'lucide-react';

const STATUSES: { value: string; label: string }[] = [
  { value: 'all', label: 'All Statuses' },
  { value: 'pass', label: 'Pass' },
  { value: 'fail', label: 'Fail' },
  { value: 'pending', label: 'Pending' },
  { value: 'expired', label: 'Expired' },
];

export default function AssetsPage() {
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [buildingFilter, setBuildingFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [search, setSearch] = useState('');

  const filtered = assets.filter(a => {
    if (tradeFilter !== 'all' && a.trade !== tradeFilter) return false;
    if (buildingFilter !== 'all' && a.buildingId !== buildingFilter) return false;
    if (statusFilter !== 'all' && a.status !== statusFilter) return false;
    if (search && !a.tag.toLowerCase().includes(search.toLowerCase()) && !a.type.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Filters */}
      <GlassCard padding="sm" className="flex flex-wrap gap-3 items-center">
        <div className="relative flex items-center">
          <Search className="absolute left-2.5 size-3.5 text-[var(--color-text-muted)]" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Tag or type…"
            className="h-8 w-40 rounded-lg border border-[var(--color-border)] bg-white/5 pl-8 pr-3 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-accent-primary)]/50 transition-colors"
          />
        </div>
        {/* Trade — driven by TRADES constant, adding a trade here is a data change only */}
        <select
          value={tradeFilter}
          onChange={e => setTradeFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          <option value="all">All Trades</option>
          {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        <select
          value={buildingFilter}
          onChange={e => setBuildingFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          <option value="all">All Buildings</option>
          {buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          {STATUSES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
        </select>
        <span className="ml-auto text-xs text-[var(--color-text-muted)]">{filtered.length} asset{filtered.length !== 1 ? 's' : ''}</span>
      </GlassCard>

      {/* Assets Table */}
      <GlassCard padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                {['Tag', 'Building', 'Trade', 'Type', 'Status', 'Last Checked', 'Next Due'].map(col => (
                  <th key={col} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(asset => {
                const building = getBuildingById(asset.buildingId);
                const sc = getAssetStatusColor(asset.status);
                return (
                  <tr key={asset.id} className="border-b border-[var(--color-border)]/50 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3"><AssetTag tag={asset.tag} /></td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{building?.name ?? '—'}</td>
                    <td className="px-4 py-3"><TradeBadge trade={asset.trade} size="sm" /></td>
                    <td className="px-4 py-3 text-[var(--color-text-primary)]">{asset.type}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${sc.text} ${sc.bg}`}>
                        {sc.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{formatDate(asset.lastChecked)}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{formatDate(asset.nextDue)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="py-12 text-center text-sm text-[var(--color-text-muted)]">
              No assets match the current filters.
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
