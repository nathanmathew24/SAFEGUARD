'use client';
// shadcn: Select, Card, Button — Documents: certificates and reports organized by trade and date
// Screen 2 (Owner) — Documents: read-only certificate/report downloads, filterable by trade and year
import { useState } from 'react';
import { reports, TRADES } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { formatDate } from '@/lib/utils';
import type { TradeType } from '@/lib/types';
import { Download, FileText, Filter } from 'lucide-react';

const OWNER_BUILDING_ID = 'bld-001';

export default function OwnerDocumentsPage() {
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [yearFilter, setYearFilter] = useState<string>('all');

  const ownerReports = reports.filter(r => r.buildingId === OWNER_BUILDING_ID);

  const filtered = ownerReports.filter(r => {
    if (tradeFilter !== 'all' && !r.trades.includes(tradeFilter as TradeType)) return false;
    if (yearFilter !== 'all' && !r.generatedAt.startsWith(yearFilter)) return false;
    return true;
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text-primary)]">Documents</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Compliance certificates and inspection reports</p>
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
          <Filter className="size-3.5" />
        </div>
        <select
          value={tradeFilter}
          onChange={e => setTradeFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          <option value="all">All Trades</option>
          {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        <select
          value={yearFilter}
          onChange={e => setYearFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          <option value="all">All Years</option>
          <option value="2026">2026</option>
          <option value="2025">2025</option>
        </select>
      </div>

      {/* Documents list */}
      {filtered.length === 0 ? (
        <div className="py-16 text-center">
          <FileText className="mx-auto size-10 text-[var(--color-text-subtle)] mb-3" />
          <p className="text-sm text-[var(--color-text-muted)]">No documents match the current filters.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(report => (
            <GlassCard key={report.id} padding="md" className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-accent-glow)] shrink-0">
                <FileText className="size-5 text-[var(--color-accent-primary)]" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-[var(--color-text-primary)] text-sm">{report.title}</p>
                <div className="flex items-center gap-2 mt-1 flex-wrap">
                  {report.trades.map(t => <TradeBadge key={t} trade={t} size="sm" />)}
                  <span className="text-[11px] text-[var(--color-text-muted)]">
                    {formatDate(report.dateRange.from)} – {formatDate(report.dateRange.to)}
                  </span>
                </div>
                <p className="mt-0.5 text-[11px] text-[var(--color-text-subtle)]">Generated {formatDate(report.generatedAt)}</p>
              </div>
              <button className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-[var(--color-accent-primary)]/30 bg-[var(--color-accent-glow)] text-[var(--color-accent-primary)] hover:bg-[var(--color-accent-primary)] hover:text-white transition-colors">
                <Download className="size-4" />
              </button>
            </GlassCard>
          ))}
        </div>
      )}

      <p className="text-center text-xs text-[var(--color-text-subtle)]">
        All documents are read-only · Emirates Safety Systems
      </p>
    </div>
  );
}
