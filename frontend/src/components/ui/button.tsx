import * as React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
        "inline-flex items-center justify-center rounded-lg text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
        // Variants
          variant === 'default' && "bg-[#4A90E2] text-white shadow-sm hover:bg-[#3f82cf]",
          variant === 'destructive' && "bg-[#E74C3C] text-white shadow-sm hover:bg-[#d44334]",
          variant === 'outline' && "border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 hover:text-slate-900",
          variant === 'secondary' && "bg-slate-100 text-slate-700 shadow-sm hover:bg-slate-200",
          variant === 'ghost' && "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
          variant === 'link' && "text-[#4A90E2] underline-offset-4 hover:underline",
          // Sizes
          size === 'default' && "h-11 px-4 py-2",
          size === 'sm' && "h-10 rounded-lg px-3 text-sm",
          size === 'lg' && "h-12 rounded-lg px-6",
          size === 'icon' && "h-10 w-10",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };

