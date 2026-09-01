// Custom composition: Badge + Progress + state for offline queue indicator
import { cn } from '@/lib/utils';
import { CloudOff, CheckCircle2, RefreshCw } from 'lucide-react';

interface SyncIndicatorProps {
  queued: number;
  synced: number;
  syncing?: boolean;
  size?: 'sm' | 'default' | 'lg';
  className?: string;
}

export function SyncIndicator({ queued, synced, syncing = false, size = 'default', className }: SyncIndicatorProps) {
  const isAllSynced = queued === 0;

  if (size === 'lg') {
    return (
      <div className={cn('flex flex-col gap-2', className)}>
        <div className={cn(
          'flex items-center gap-2 rounded-xl px-4 py-3',
          isAllSynced ? 'bg-[var(--color-status-ok-bg)]' : 'bg-[var(--color-status-warning-bg)]'
        )}>
          {syncing ? (
            <RefreshCw className="size-5 animate-spin text-[var(--color-status-warning)]" />
          ) : isAllSynced ? (
            <CheckCircle2 className="size-5 text-[var(--color-status-ok)]" />
          ) : (
            <CloudOff className="size-5 text-[var(--color-status-warning)]" />
          )}
          <div>
            <p className={cn(
              'text-sm font-semibold',
              isAllSynced ? 'text-[var(--color-status-ok)]' : 'text-[var(--color-status-warning)]'
            )}>
              {syncing ? 'Syncing…' : isAllSynced ? 'All synced' : `${queued} result${queued !== 1 ? 's' : ''} queued`}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {synced} synced & locked · {queued} pending upload
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <span className={cn(
      'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
      isAllSynced
        ? 'bg-[var(--color-status-ok-bg)] text-[var(--color-status-ok)]'
        : 'bg-[var(--color-status-warning-bg)] text-[var(--color-status-warning)]',
      className
    )}>
      {isAllSynced ? (
        <CheckCircle2 className="size-3" />
      ) : (
        <span className="size-1.5 rounded-full bg-[var(--color-status-warning)] animate-pulse" />
      )}
      {isAllSynced ? 'Synced' : `${queued} queued`}
    </span>
  );
}
