import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { StatusType, TradeType, AssetStatus, IssuePriority } from './types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getStatusColor(status: StatusType) {
  const map = {
    ok: {
      text: 'text-[var(--color-status-ok)]',
      bg: 'bg-[var(--color-status-ok-bg)]',
      dot: 'bg-[var(--color-status-ok)]',
      border: 'border-[var(--color-status-ok)]/30',
      label: 'OK',
    },
    warning: {
      text: 'text-[var(--color-status-warning)]',
      bg: 'bg-[var(--color-status-warning-bg)]',
      dot: 'bg-[var(--color-status-warning)]',
      border: 'border-[var(--color-status-warning)]/30',
      label: 'Attention',
    },
    critical: {
      text: 'text-[var(--color-status-critical)]',
      bg: 'bg-[var(--color-status-critical-bg)]',
      dot: 'bg-[var(--color-status-critical)]',
      border: 'border-[var(--color-status-critical)]/30',
      label: 'Critical',
    },
  };
  return map[status];
}

export function getTradeColor(trade: TradeType) {
  const map = {
    fire: { text: 'text-orange-400', bg: 'bg-orange-400/10', border: 'border-orange-400/20', label: 'Fire' },
    hvac: { text: 'text-sky-400', bg: 'bg-sky-400/10', border: 'border-sky-400/20', label: 'HVAC' },
    elv: { text: 'text-violet-400', bg: 'bg-violet-400/10', border: 'border-violet-400/20', label: 'ELV' },
  };
  return map[trade];
}

export function getAssetStatusColor(status: AssetStatus) {
  const map = {
    pass: { text: 'text-[var(--color-status-ok)]', bg: 'bg-[var(--color-status-ok-bg)]', label: 'Pass' },
    fail: { text: 'text-[var(--color-status-critical)]', bg: 'bg-[var(--color-status-critical-bg)]', label: 'Fail' },
    pending: { text: 'text-[var(--color-status-warning)]', bg: 'bg-[var(--color-status-warning-bg)]', label: 'Pending' },
    expired: { text: 'text-[var(--color-status-critical)]', bg: 'bg-[var(--color-status-critical-bg)]', label: 'Expired' },
  };
  return map[status];
}

export function getPriorityStatus(priority: IssuePriority): StatusType {
  const map: Record<IssuePriority, StatusType> = {
    high: 'critical',
    medium: 'warning',
    low: 'ok',
  };
  return map[priority];
}

export function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-AE', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
}

export function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-AE', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

export function getDaysUntil(iso: string) {
  const diff = new Date(iso).getTime() - Date.now();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

export function getInitials(name: string) {
  return name.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2);
}

export function getStatusLabel(status: StatusType): string {
  const labels: Record<StatusType, string> = { ok: 'OK', warning: 'Attention', critical: 'Critical' };
  return labels[status];
}
