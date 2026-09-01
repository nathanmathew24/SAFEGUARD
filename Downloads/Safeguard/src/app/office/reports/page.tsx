'use client';
// shadcn: Table, Select, Button, Dialog — Reports list with filters and pack generation
// Screen 6 — Reports: filterable compliance reports + one-click renewal pack export
import { useState } from 'react';
import { reports, buildings, TRADES, getBuildingById } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { formatDate } from '@/lib/utils';
import type { TradeType } from '@/lib/types';
import { Download, FileText, Plus, X, Check } from 'lucide-react';

export default function ReportsPage() {
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [buildingFilter, setBuildingFilter] = useState<string>('all');
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [genBuilding, setGenBuilding] = useState(buildings[0].id);
  const [genTrades, setGenTrades] = useState<TradeType[]>(['fire']);
  const [generated, setGenerated] = useState(false);

  const filtered = reports.filter(r => {
    if (buildingFilter !== 'all' && r.buildingId !== buildingFilter) return false;
    if (tradeFilter !== 'all' && !r.trades.includes(tradeFilter as TradeType)) return false;
    return true;
  });

  const toggleTrade = (t: TradeType) =>
    setGenTrades(prev => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]);

  const handleGenerate = () => {
    setGenerated(true);
    setTimeout(() => {
      setGenerated(false);
      setShowGenerateDialog(false);
    }, 1800);
  };

  return (
    <div className="space-y-4">
      {/* Generate Dialog */}
      {showGenerateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Generate Renewal Pack</h2>
              <button onClick={() => setShowGenerateDialog(false)} className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]">
                <X className="size-4" />
              </button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-[var(--color-text-muted)]">Building</label>
                <select
                  value={genBuilding}
                  onChange={e => setGenBuilding(e.target.value)}
                  className="mt-1 w-full h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none"
                >
                  {buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-[var(--color-text-muted)]">Trades</label>
                <div className="mt-1.5 flex gap-2 flex-wrap">
                  {TRADES.map(t => (
                    <button
                      key={t.id}
                      onClick={() => toggleTrade(t.id)}
                      className={`flex items-center gap-1 rounded-lg px-2 py-1 text-xs border transition-colors ${genTrades.includes(t.id) ? 'border-[var(--color-accent-primary)] bg-[var(--color-accent-glow)] text-[var(--color-accent-primary)]' : 'border-[var(--color-border)] bg-white/5 text-[var(--color-text-muted)]'}`}
                    >
                      {genTrades.includes(t.id) && <Check className="size-3" />}
                      {t.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <button
              onClick={handleGenerate}
              disabled={genTrades.length === 0 || generated}
              className="w-full rounded-lg bg-[var(--color-accent-primary)] py-2 text-xs font-medium text-white hover:bg-[var(--color-accent-primary-hover)] disabled:opacity-50 transition-colors"
            >
              {generated ? '✓ Pack generated!' : 'Generate Pack'}
            </button>
          </div>
        </div>
      )}

      {/* Filters + action */}
      <GlassCard padding="sm" className="flex flex-wrap gap-3 items-center">
        <select
          value={buildingFilter}
          onChange={e => setBuildingFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none"
        >
          <option value="all">All Buildings</option>
          {buildings.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <select
          value={tradeFilter}
          onChange={e => setTradeFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none"
        >
          <option value="all">All Trades</option>
          {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        <button
          onClick={() => setShowGenerateDialog(true)}
          className="ml-auto flex items-center gap-1.5 rounded-lg bg-[var(--color-accent-primary)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-accent-primary-hover)] transition-colors"
        >
          <Plus className="size-3.5" /> Generate Renewal Pack
        </button>
      </GlassCard>

      {/* Reports table */}
      <GlassCard padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                {['Title', 'Building', 'Trades', 'Date Range', 'Generated', ''].map(col => (
                  <th key={col} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(report => {
                const building = getBuildingById(report.buildingId);
                return (
                  <tr key={report.id} className="border-b border-[var(--color-border)]/50 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="size-4 text-[var(--color-text-muted)]" />
                        <span className="font-medium text-[var(--color-text-primary)]">{report.title}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{building?.name}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {report.trades.map(t => <TradeBadge key={t} trade={t} size="sm" />)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">
                      {formatDate(report.dateRange.from)} – {formatDate(report.dateRange.to)}
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{formatDate(report.generatedAt)}</td>
                    <td className="px-4 py-3">
                      <button className="flex items-center gap-1 text-[var(--color-accent-primary)] hover:underline">
                        <Download className="size-3.5" /> Download
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="py-12 text-center text-sm text-[var(--color-text-muted)]">No reports match the current filters.</div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
