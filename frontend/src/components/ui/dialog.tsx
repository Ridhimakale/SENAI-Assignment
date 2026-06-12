import * as React from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";
import { Button } from "./button";

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export function Dialog({ isOpen, onClose, title, children }: DialogProps) {
  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleEscape);
    }
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-neutral-950/30 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />
      {/* Content */}
      <div className="relative z-10 w-full max-w-lg rounded-lg border border-border bg-background p-5 shadow-lg animate-in fade-in zoom-in-95 duration-100">
        <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
          {title && <h3 className="text-sm font-semibold text-foreground tracking-tight">{title}</h3>}
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
            <X size={14} />
          </Button>
        </div>
        <div className="text-xs text-foreground">{children}</div>
      </div>
    </div>,
    document.body
  );
}
