'use client';
// shadcn: Calendar, Tabs, Badge, Sheet — Schedule with Month/Agenda toggle
// Screen 4 — Schedule: calendar-first view with day status dots + agenda list
import { useState } from 'react';
import { visits, getBuildingById, getTechnicianById, TRADES } from '@/lib/mockData';
import { GlassCard } from '@/components/shared/GlassCard';
import { TradeBadge } from '@/components/shared/TradeBadge';
import { VisitStatusBadge } from '@/components/shared/VisitStatusBadge';
import { formatDate } from '@/lib/utils';
import type { TradeType } from '@/lib/types';
import { CalendarDays, List, Clock } from 'lucide-react';

// Generate calendar for Sep 2026
const YEAR = 2026;
const MONTH = 8; // September (0-indexed)
const TODAY = '2026-09-01';

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate();
}
function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay(); // 0=Sun
}

function dateStr(year: number, month: number, day: number) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

export default function SchedulePage() {
  const [view, setView] = useState<'month' | 'agenda'>('month');
  const [selectedDate, setSelectedDate] = useState<string | null>(TODAY);
  const [tradeFilter, setTradeFilter] = useState<string>('all');

  const daysInMonth = getDaysInMonth(YEAR, MONTH);
  const firstDay = getFirstDayOfMonth(YEAR, MONTH);

  // Compute status dot for each day
  const dayStatusMap: Record<string, 'ok' | 'warning' | 'critical'> = {};
  visits.forEach(v => {
    if (!v.scheduledDate.startsWith('2026-09')) return;
    const prev = dayStatusMap[v.scheduledDate];
    const next = v.status === 'overdue' ? 'critical' : v.status === 'completed' ? 'ok' : 'warning';
    if (!prev || (next === 'critical') || (next === 'warning' && prev === 'ok')) {
      dayStatusMap[v.scheduledDate] = next;
    }
  });

  const dayVisits = selectedDate
    ? visits.filter(v => v.scheduledDate === selectedDate && (tradeFilter === 'all' || v.trade === tradeFilter))
    : [];

  const agendaVisits = visits
    .filter(v => v.scheduledDate >= TODAY && (tradeFilter === 'all' || v.trade === tradeFilter))
    .sort((a, b) => a.scheduledDate.localeCompare(b.scheduledDate));

  const statusDotClass: Record<string, string> = {
    ok: 'bg-[var(--color-status-ok)]',
    warning: 'bg-[var(--color-status-warning)]',
    critical: 'bg-[var(--color-status-critical)]',
  };

  return (
    <div className="space-y-4">
      {/* View toggle + trade filter */}
      <div className="flex items-center gap-3">
        <div className="flex rounded-lg border border-[var(--color-border)] overflow-hidden">
          <button
            onClick={() => setView('month')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs transition-colors ${view === 'month' ? 'bg-[var(--color-accent-primary)] text-white' : 'bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'}`}
          >
            <CalendarDays className="size-3.5" /> Month
          </button>
          <button
            onClick={() => setView('agenda')}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs transition-colors ${view === 'agenda' ? 'bg-[var(--color-accent-primary)] text-white' : 'bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'}`}
          >
            <List className="size-3.5" /> Agenda
          </button>
        </div>
        <select
          value={tradeFilter}
          onChange={e => setTradeFilter(e.target.value)}
          className="h-8 rounded-lg border border-[var(--color-border)] bg-[#0a0c12] px-2 text-xs text-[var(--color-text-primary)] outline-none focus:border-[var(--color-accent-primary)]/50"
        >
          <option value="all">All Trades</option>
          {TRADES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
        </select>
      </div>

      {view === 'month' ? (
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Calendar */}
          <GlassCard padding="md" className="lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">September 2026</h3>
            </div>
            <div className="grid grid-cols-7 gap-1 text-center">
              {['Su','Mo','Tu','We','Th','Fr','Sa'].map(d => (
                <div key={d} className="py-1 text-[10px] font-medium text-[var(--color-text-subtle)]">{d}</div>
              ))}
              {/* Blank cells for first day offset */}
              {Array.from({ length: firstDay }).map((_, i) => <div key={`blank-${i}`} />)}
              {/* Day cells */}
              {Array.from({ length: daysInMonth }).map((_, i) => {
                const day = i + 1;
                const ds = dateStr(YEAR, MONTH, day);
                const status = dayStatusMap[ds];
                const isToday = ds === TODAY;
                const isSelected = ds === selectedDate;
                return (
                  <button
                    key={day}
                    onClick={() => setSelectedDate(ds)}
                    className={`relative flex flex-col items-center rounded-lg py-1.5 text-xs transition-colors ${isSelected ? 'bg-[var(--color-accent-primary)] text-white' : isToday ? 'bg-white/10 text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)] hover:bg-white/5 hover:text-[var(--color-text-primary)]'}`}
                  >
                    {day}
                    {status && (
                      <span className={`mt-0.5 h-1 w-1 rounded-full ${isSelected ? 'bg-white' : statusDotClass[status]}`} />
                    )}
                  </button>
                );
              })}
            </div>
          </GlassCard>

          {/* Day panel */}
          <GlassCard padding="md" className="flex flex-col gap-3">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
              {selectedDate ? formatDate(selectedDate) : 'Select a day'}
            </h3>
            {dayVisits.length === 0 ? (
              <p className="text-xs text-[var(--color-text-muted)]">No visits scheduled{selectedDate ? ' this day.' : '.'}</p>
            ) : (
              <div className="space-y-2">
                {dayVisits.map(v => {
                  const building = getBuildingById(v.buildingId);
                  const tech = getTechnicianById(v.technicianId);
                  return (
                    <div key={v.id} className="rounded-xl bg-white/[0.03] p-3 space-y-2 border border-[var(--color-border)]">
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-xs font-medium text-[var(--color-text-primary)]">{building?.name}</p>
                        <VisitStatusBadge status={v.status} />
                      </div>
                      <TradeBadge trade={v.trade} size="sm" />
                      <div className="flex items-center gap-1.5 text-[11px] text-[var(--color-text-muted)]">
                        <Clock className="size-3" /> {v.scheduledTime}
                      </div>
                      {tech && (
                        <div className="flex items-center gap-1.5">
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-400">{tech.initials}</span>
                          <span className="text-[11px] text-[var(--color-text-muted)]">{tech.name}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </GlassCard>
        </div>
      ) : (
        /* Agenda view */
        <GlassCard padding="none" className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  {['Date', 'Building', 'Trade', 'Time', 'Technician', 'Status'].map(col => (
                    <th key={col} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)]">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {agendaVisits.map(v => {
                  const building = getBuildingById(v.buildingId);
                  const tech = getTechnicianById(v.technicianId);
                  return (
                    <tr key={v.id} className="border-b border-[var(--color-border)]/50 hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 py-3 text-[var(--color-text-primary)] font-medium">{formatDate(v.scheduledDate)}</td>
                      <td className="px-4 py-3 text-[var(--color-text-muted)]">{building?.name}</td>
                      <td className="px-4 py-3"><TradeBadge trade={v.trade} size="sm" /></td>
                      <td className="px-4 py-3 text-[var(--color-text-muted)]">{v.scheduledTime}</td>
                      <td className="px-4 py-3">
                        {tech && (
                          <div className="flex items-center gap-1.5">
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-bold text-indigo-400">{tech.initials}</span>
                            <span className="text-[var(--color-text-muted)]">{tech.name}</span>
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3"><VisitStatusBadge status={v.status} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
