'use client';
// shadcn: Tabs, Table, Switch, Dialog, Select — Rules & Settings
// Screen 8 — Rules & Settings: inspection rules (emirate × trade) + workspace settings
import { useState } from 'react';
import { inspectionRules, TRADES } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import type { TradeType, Emirate } from '@/lib/types';
import { Settings, Shield, Plus } from 'lucide-react';

const EMIRATES: Emirate[] = ['Dubai', 'Sharjah', 'Abu Dhabi'];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'rules' | 'workspace'>('rules');
  const [emirateFilter, setEmirateFilter] = useState<string>('all');
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  // Workspace state
  const [enabledTrades, setEnabledTrades] = useState<Record<TradeType, boolean>>({
    fire: true, hvac: true, elv: true,
  });

  const filteredRules = inspectionRules.filter(r => {
    if (emirateFilter !== 'all' && r.emirate !== emirateFilter) return false;
    if (tradeFilter !== 'all' && r.trade !== tradeFilter) return false;
    return true;
  });

  const toggleTrade = (t: TradeType) =>
    setEnabledTrades(prev => ({ ...prev, [t]: !prev[t] }));

  return (
    <div className="space-y-4">
      {/* Tab toggle */}
      <div className="flex rounded-lg border border-[var(--color-border)] overflow-hidden w-fit">
        <button
          onClick={() => setActiveTab('rules')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs transition-colors ${activeTab === 'rules' ? 'bg-[var(--color-accent-primary)] text-white' : 'bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'}`}
        >
          <Shield className="size-3.5" /> Inspection Rules
        </button>
        <button
          onClick={() => setActiveTab('workspace')}
          className={`flex items-center gap-1.5 px-4 py-2 text-xs transition-colors ${activeTab === 'workspace' ? 'bg-[var(--color-accent-primary)] text-white' : 'bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'}`}
        >
          <Settings className="size-3.5" /> Workspace
        </button>
      </div>

      {activeTab === 'rules' ? (
        <>
          {/* Rules filters */}
          <GlassCard padding="sm" className="flex flex-wrap gap-3 items-center">
            <select value={emirateFilter} onChange={e => setEmirateFilter(e.target.value)}
              className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none">
              <option value="all">All Emirates</option>
              {EMIRATES.map(e => <option key={e} value={e}>{e}</option>)}
            </select>
            <select value={tradeFilter} onChange={e => setTradeFilter(e.target.value)}
              className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none">
              <option value="all">All Trades</option>
              {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
            </select>
            <span className="text-xs text-[var(--color-text-muted)]">{filteredRules.length} rules</span>
            <button className="ml-auto flex items-center gap-1.5 rounded-lg bg-[var(--color-accent-primary)] px-3 py-1.5 text-xs font-medium text-white hover:bg-[var(--color-accent-primary-hover)] transition-colors">
              <Plus className="size-3.5" /> Add Rule
            </button>
          </GlassCard>

          {/* Rules Table — keyed by emirate × trade */}
          <GlassCard padding="none" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    {['Emirate', 'Trade', 'Asset Type', 'Frequency', 'Governing Standard'].map(col => (
                      <th key={col} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredRules.map(rule => (
                    <tr key={rule.id} className="border-b border-[var(--color-border)]/50 hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 py-3 text-[var(--color-text-primary)] font-medium">{rule.emirate}</td>
                      <td className="px-4 py-3"><TradeBadge trade={rule.trade} size="sm" /></td>
                      <td className="px-4 py-3 text-[var(--color-text-muted)]">{rule.assetType}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-[var(--color-accent-glow)] px-2 py-0.5 text-[10px] font-medium text-[var(--color-accent-primary)]">
                          Every {rule.frequencyDays}d
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[var(--color-text-muted)]">{rule.standard}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      ) : (
        /* Workspace tab */
        <div className="grid gap-4 lg:grid-cols-2">
          <GlassCard padding="md" className="space-y-4">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Tenant Settings</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-[var(--color-text-muted)]">Company Name</label>
                <input
                  defaultValue="Emirates Safety Systems"
                  className="mt-1 w-full h-8 rounded-lg border border-[var(--color-border)] bg-white/5 px-3 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50 transition-colors"
                />
              </div>
              <div>
                <label className="text-xs text-[var(--color-text-muted)]">Primary Emirate</label>
                <select className="mt-1 w-full h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none">
                  <option>Dubai</option>
                  <option>Sharjah</option>
                  <option>Abu Dhabi</option>
                </select>
              </div>
            </div>
          </GlassCard>

          <GlassCard padding="md" className="space-y-4">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">Active Trades</h3>
            <p className="text-xs text-[var(--color-text-muted)]">Enable or disable which trades this tenant handles.</p>
            <div className="space-y-3">
              {TRADES.map(trade => (
                <div key={trade.id} className="flex items-center justify-between rounded-lg bg-white/[0.02] px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <TradeBadge trade={trade.id} size="sm" />
                    <span className="text-xs text-[var(--color-text-muted)]">{trade.description}</span>
                  </div>
                  <button
                    onClick={() => toggleTrade(trade.id)}
                    className={`relative h-5 w-9 rounded-full transition-colors ${enabledTrades[trade.id] ? 'bg-[var(--color-accent-primary)]' : 'bg-white/10'}`}
                  >
                    <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${enabledTrades[trade.id] ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </button>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
