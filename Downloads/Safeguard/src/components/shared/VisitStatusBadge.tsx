// Custom composition: Visit status pill using status tokens
import { cn } from '@/lib/utils';
import type { VisitStatus } from '@/lib/types';

const styles: Record<VisitStatus, { text: string; bg: string; dot: string; label: string }> = {
  scheduled: {
    text: 'text-sky-400', bg: 'bg-sky-400/10', dot: 'bg-sky-400', label: 'Scheduled',
  },
  'in-progress': {
    text: 'text-[var(--color-accent-primary)]', bg: 'bg-[var(--color-accent-glow)]', dot: 'bg-[var(--color-accent-primary)]', label: 'In Progress',
  },
  completed: {
    text: 'text-[var(--color-status-ok)]', bg: 'bg-[var(--color-status-ok-bg)]', dot: 'bg-[var(--color-status-ok)]', label: 'Completed',
  },
  overdue: {
    text: 'text-[var(--color-status-critical)]', bg: 'bg-[var(--color-status-critical-bg)]', dot: 'bg-[var(--color-status-critical)]', label: 'Overdue',
  },
};

export function VisitStatusBadge({ status, className }: { status: VisitStatus; className?: string }) {
  const s = styles[status];
  return (
    <span className={cn(
      'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
      s.text, s.bg, className
    )}>
      <span className={cn('size-1.5 rounded-full', s.dot, status === 'in-progress' && 'animate-pulse')} />
      {s.label}
    </span>
  );
}
