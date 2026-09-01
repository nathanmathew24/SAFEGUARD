// shadcn: Card (wrapped with glass treatment)
import { cn } from '@/lib/utils';

interface GlassCardProps extends React.ComponentProps<'div'> {
  padding?: 'sm' | 'md' | 'lg' | 'none';
}

export function GlassCard({ className, padding = 'md', children, ...props }: GlassCardProps) {
  const padMap = { none: '', sm: 'p-3', md: 'p-4', lg: 'p-6' };
  return (
    <div
      className={cn(
        'glass-card',
        padMap[padding],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function GlassCardHeader({ className, children, ...props }: React.ComponentProps<'div'>) {
  return <div className={cn('mb-3 flex items-center justify-between', className)} {...props}>{children}</div>;
}

export function GlassCardTitle({ className, children, ...props }: React.ComponentProps<'p'>) {
  return <p className={cn('text-sm font-semibold text-[var(--color-text-primary)]', className)} {...props}>{children}</p>;
}

export function GlassCardContent({ className, children, ...props }: React.ComponentProps<'div'>) {
  return <div className={cn('', className)} {...props}>{children}</div>;
}
