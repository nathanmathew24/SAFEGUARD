// Custom composition: styled span for asset tag chips (EX-014, AHU-03 etc)
import { cn } from '@/lib/utils';

export function AssetTag({ tag, className }: { tag: string; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border border-[var(--color-border-strong)] bg-[rgba(255,255,255,0.04)] px-1.5 py-0.5 font-mono text-xs font-medium text-[var(--color-text-primary)]',
        className
      )}
    >
      {tag}
    </span>
  );
}
