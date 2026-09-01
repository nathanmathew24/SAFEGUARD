import { cn, getStatusColor, getStatusLabel } from "@/lib/utils";
import { StatusType } from "@/lib/types";

interface Props {
  status: StatusType;
  showLabel?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function HealthIndicator({
  status,
  showLabel = true,
  size = "md",
  className,
}: Props) {
  const colors = getStatusColor(status);
  const dotSize = size === "sm" ? "w-2 h-2" : size === "lg" ? "w-3 h-3" : "w-2.5 h-2.5";
  const textSize = size === "sm" ? "text-xs" : size === "lg" ? "text-sm" : "text-xs";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className={cn("rounded-full flex-shrink-0", dotSize, colors.dot)} />
      {showLabel && (
        <span className={cn("font-medium", textSize, colors.text)}>
          {getStatusLabel(status)}
        </span>
      )}
    </div>
  );
}
