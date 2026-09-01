// shadcn: Badge (trade variant: fire=orange, hvac=sky, elv=violet)
import { cn } from '@/lib/utils';
import { getTradeColor } from '@/lib/utils';
import type { TradeType } from '@/lib/types';
import { Flame, Wind, Radio } from 'lucide-react';

interface TradeBadgeProps {
  trade: TradeType;
  className?: string;
  size?: 'sm' | 'default';
  showIcon?: boolean;
}

const icons: Record<TradeType, React.ComponentType<{ className?: string }>> = {
  fire: Flame,
  hvac: Wind,
  elv: Radio,
};

export function TradeBadge({ trade, className, size = 'default', showIcon = true }: TradeBadgeProps) {
  const colors = getTradeColor(trade);
  const Icon = icons[trade];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border font-medium',
        colors.text, colors.bg, colors.border,
        size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs',
        className
      )}
    >
      {showIcon && <Icon className={size === 'sm' ? 'size-2.5' : 'size-3'} />}
      {colors.label}
    </span>
  );
}
