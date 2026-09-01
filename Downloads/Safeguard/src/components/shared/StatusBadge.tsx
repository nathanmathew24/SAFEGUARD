// shadcn: Badge (status variant using status CSS tokens)
import { cn } from '@/lib/utils';
import { getStatusColor } from '@/lib/utils';
import type { StatusType } from '@/lib/types';

interface StatusBadgeProps {
  status: StatusType;
  className?: string;
  size?: 'sm' | 'default';
}

export function StatusBadge({ status, className, size = 'default' }: StatusBadgeProps) {
  const colors = getStatusColor(status);
  const labels: Record<StatusType, string> = { ok: 'OK', warning: 'Attention', critical: 'Critical' };
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border font-medium',
        colors.text, colors.bg, colors.border,
        size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs',
        className
      )}
    >
      <span className={cn('rounded-full', colors.dot, size === 'sm' ? 'size-1' : 'size-1.5')} />
      {labels[status]}
    </span>
  );
}
