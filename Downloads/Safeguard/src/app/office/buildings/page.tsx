'use client';
// shadcn: Table, Select, Input, Badge — Buildings list with filters
// Screen 2 — Buildings list + filterable table
import { useState } from 'react';
import Link from 'next/link';
import { buildings, technicians, getTechnicianById } from '@/lib/mockData';
import { TRADES } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { formatDate } from '@/lib/utils';
import type { TradeType, StatusType, Emirate } from '@/lib/types';
import { Search, ArrowRight, Building2 } from 'lucide-react';

const EMIRATES = ['All', 'Dubai', 'Sharjah', 'Abu Dhabi'] as const;
const STATUSES = ['All', 'ok', 'warning', 'critical'] as const;

export default function BuildingsPage() {
  const [emirateFilter, setEmirateFilter] = useState<string>('All');
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [search, setSearch] = useState('');

  const filtered = buildings.filter(b => {
    if (emirateFilter !== 'All' && b.emirate !== emirateFilter) return false;
    if (tradeFilter !== 'all' && !b.trades.includes(tradeFilter as TradeType)) return false;
    if (statusFilter !== 'All' && b.health !== statusFilter) return false;
    if (search && !b.name.toLowerCase().includes(search.toLowerCase())) return false;
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
            placeholder="Search buildings…"
            className="h-8 w-44 rounded-lg border border-[var(--color-border)] bg-white/5 pl-8 pr-3 text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none focus:border-[var(--color-accent-primary)]/50 transition-colors"
          />
        </div>
        {/* Emirate filter */}
        <select
          value={emirateFilter}
          onChange={e => setEmirateFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          {EMIRATES.map(e => <option key={e} value={e}>{e === 'All' ? 'All Emirates' : e}</option>)}
        </select>
        {/* Trade filter */}
        <select
          value={tradeFilter}
          onChange={e => setTradeFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          <option value="all">All Trades</option>
          {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        {/* Status filter */}
        <select
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          {STATUSES.map(s => <option key={s} value={s}>{s === 'All' ? 'All Statuses' : s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
        </select>
        <span className="ml-auto text-xs text-[var(--color-text-muted)]">{filtered.length} building{filtered.length !== 1 ? 's' : ''}</span>
      </GlassCard>

      {/* Table */}
      <GlassCard padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                {['Building', 'Emirate', 'Health', 'Trades', 'Next Inspection', 'Assets', 'Technicians', ''].map(col => (
                  <th key={col} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(building => {
                const techs = building.assignedTechnicianIds.map(id => getTechnicianById(id)).filter(Boolean);
                return (
                  <tr key={building.id} className="border-b border-[var(--color-border)]/50 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-[var(--color-text-primary)]">{building.name}</p>
                        <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{building.address.substring(0, 40)}…</p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{building.emirate}</td>
                    <td className="px-4 py-3"><StatusBadge status={building.health} size="sm" /></td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {building.trades.map(t => <TradeBadge key={t} trade={t} size="sm" />)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{formatDate(building.nextInspection)}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{building.assetCount}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {techs.map(t => t && (
                          <span key={t.id} className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-400" title={t.name}>
                            {t.initials}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/office/buildings/${building.id}`} className="flex items-center gap-1 text-[var(--color-accent-primary)] hover:underline">
                        View <ArrowRight className="size-3" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="py-12 text-center text-sm text-[var(--color-text-muted)]">
              No buildings match the current filters.
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
