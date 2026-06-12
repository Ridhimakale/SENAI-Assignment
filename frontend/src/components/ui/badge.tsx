import * as React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' | 'info';
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold transition-colors focus:outline-none",
        variant === 'default' && "border-transparent bg-[#4A90E2] text-white",
        variant === 'secondary' && "border-transparent bg-slate-100 text-slate-700",
        variant === 'destructive' && "border-transparent bg-[#E74C3C] text-white",
        variant === 'outline' && "text-slate-700 border-slate-200 bg-white",
        variant === 'success' && "border-transparent bg-[#36C275] text-white",
        variant === 'warning' && "border-transparent bg-[#F5A623] text-white",
        variant === 'info' && "border-transparent bg-[#6AA9FF] text-white",
        className
      )}
      {...props}
    />
  );
}

export { Badge };

