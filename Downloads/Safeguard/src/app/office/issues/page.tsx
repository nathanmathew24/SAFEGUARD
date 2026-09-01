'use client';
// shadcn: Table, Select, Badge, Dialog — Issues & Alerts with resolve/assign actions
// Screen 7 — Issues & Alerts: failed assets, expired certs, overdue inspections
import { useState } from 'react';
import { issues, assets, buildings, technicians, TRADES, getBuildingById, getAssetById, getTechnicianById } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { AssetTag } from '@/components/shared/AssetTag';
import { formatDate, getPriorityStatus } from '@/lib/utils';
import type { TradeType, IssuePriority, IssueStatus } from '@/lib/types';
import { AlertTriangle, CheckCircle2, X, UserCheck } from 'lucide-react';

const ISSUE_TYPE_LABELS: Record<string, string> = {
  'failed-asset': 'Failed Asset',
  'expired-cert': 'Expired Certificate',
  'overdue-inspection': 'Overdue Inspection',
};

export default function IssuesPage() {
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('open');
  const [localIssues, setLocalIssues] = useState(issues);
  const [assignDialog, setAssignDialog] = useState<string | null>(null);
  const [selectedTech, setSelectedTech] = useState(technicians[0].id);

  const filtered = localIssues.filter(i => {
    if (tradeFilter !== 'all' && i.trade !== tradeFilter) return false;
    if (priorityFilter !== 'all' && i.priority !== priorityFilter) return false;
    if (statusFilter !== 'all' && i.status !== statusFilter) return false;
    return true;
  });

  const handleResolve = (id: string) =>
    setLocalIssues(prev => prev.map(i => i.id === id ? { ...i, status: 'resolved' } : i));

  const handleAssign = (id: string) => {
    setLocalIssues(prev => prev.map(i => i.id === id ? { ...i, assignedToId: selectedTech, status: 'in-progress' } : i));
    setAssignDialog(null);
  };

  return (
    <div className="space-y-4">
      {/* Assign Dialog */}
      {assignDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card w-full max-w-sm p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Assign Technician</h2>
              <button onClick={() => setAssignDialog(null)}><X className="size-4 text-[var(--color-text-muted)]" /></button>
            </div>
            <select
              value={selectedTech}
              onChange={e => setSelectedTech(e.target.value)}
              className="w-full h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none"
            >
              {technicians.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
            <button
              onClick={() => handleAssign(assignDialog)}
              className="w-full rounded-lg bg-[var(--color-accent-primary)] py-2 text-xs font-medium text-white hover:bg-[var(--color-accent-primary-hover)] transition-colors"
            >
              Assign
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <GlassCard padding="sm" className="flex flex-wrap gap-3 items-center">
        <select value={tradeFilter} onChange={e => setTradeFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none">
          <option value="all">All Trades</option>
          {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
        <select value={priorityFilter} onChange={e => setPriorityFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none">
          <option value="all">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none">
          <option value="all">All Statuses</option>
          <option value="open">Open</option>
          <option value="in-progress">In Progress</option>
          <option value="resolved">Resolved</option>
        </select>
        <span className="ml-auto text-xs text-[var(--color-text-muted)]">{filtered.length} issue{filtered.length !== 1 ? 's' : ''}</span>
      </GlassCard>

      {/* Issues Table */}
      <GlassCard padding="none" className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)]">
                {['Asset', 'Building', 'Trade', 'Type', 'Priority', 'Status', 'Assigned To', 'Created', 'Actions'].map(col => (
                  <th key={col} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(issue => {
                const asset = getAssetById(issue.assetId);
                const building = getBuildingById(issue.buildingId);
                const assignedTech = issue.assignedToId ? getTechnicianById(issue.assignedToId) : null;
                const priorityStatus = getPriorityStatus(issue.priority);
                return (
                  <tr key={issue.id} className="border-b border-[var(--color-border)]/50 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">{asset ? <AssetTag tag={asset.tag} /> : '—'}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{building?.name}</td>
                    <td className="px-4 py-3"><TradeBadge trade={issue.trade} size="sm" /></td>
                    <td className="px-4 py-3 text-[var(--color-text-primary)]">{ISSUE_TYPE_LABELS[issue.type]}</td>
                    <td className="px-4 py-3"><StatusBadge status={priorityStatus} size="sm" /></td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${issue.status === 'resolved' ? 'bg-[var(--color-status-ok-bg)] text-[var(--color-status-ok)]' : issue.status === 'in-progress' ? 'bg-[var(--color-accent-glow)] text-[var(--color-accent-primary)]' : 'bg-white/5 text-[var(--color-text-muted)]'}`}>
                        {issue.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{assignedTech?.name ?? '—'}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{formatDate(issue.createdAt)}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1.5">
                        {issue.status !== 'resolved' && (
                          <>
                            <button onClick={() => setAssignDialog(issue.id)} className="flex items-center gap-1 rounded-md bg-white/5 px-2 py-1 text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors">
                              <UserCheck className="size-3" /> Assign
                            </button>
                            <button onClick={() => handleResolve(issue.id)} className="flex items-center gap-1 rounded-md bg-[var(--color-status-ok-bg)] px-2 py-1 text-[10px] text-[var(--color-status-ok)] hover:bg-[rgba(16,185,129,0.2)] transition-colors">
                              <CheckCircle2 className="size-3" /> Resolve
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="py-12 text-center text-sm text-[var(--color-text-muted)]">No issues match the current filters.</div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
