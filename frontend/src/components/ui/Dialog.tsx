"use client";

import React from "react";
import { Dialog as DialogPrimitive } from "radix-ui";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

interface DialogContentProps {
  title: string;
  description: string;
  children: React.ReactNode;
  className?: string;
  restoreFocusRef?: React.RefObject<HTMLElement | null>;
  fallbackFocusRef?: React.RefObject<HTMLElement | null>;
}

export function Dialog({ open, onClose, children }: DialogProps) {
  return (
    <DialogPrimitive.Root
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) onClose();
      }}
    >
      {children}
    </DialogPrimitive.Root>
  );
}

export function DialogContent({ title, description, children, className, restoreFocusRef, fallbackFocusRef }: DialogContentProps) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-sm motion-safe:animate-fade-in" />
      <DialogPrimitive.Content
        onCloseAutoFocus={(event) => {
          const restoreTarget = restoreFocusRef?.current;
          if (restoreTarget?.isConnected) {
            event.preventDefault();
            restoreTarget.focus();
          } else if (fallbackFocusRef?.current?.isConnected) {
            event.preventDefault();
            fallbackFocusRef.current.focus();
          }
        }}
        className={cn(
          "fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-surface-border bg-surface-raised p-6 shadow-xl outline-none motion-safe:animate-fade-in",
          className,
        )}
      >
        <div className="mb-5 grid grid-cols-[minmax(0,1fr)_44px] items-start gap-3">
          <div className="min-w-0 space-y-1">
            <DialogPrimitive.Title className="text-base font-bold text-claude-text">
              {title}
            </DialogPrimitive.Title>
            <DialogPrimitive.Description className="text-xs font-medium leading-relaxed text-claude-muted">
              {description}
            </DialogPrimitive.Description>
          </div>
          <DialogPrimitive.Close asChild>
            <button
              type="button"
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl text-claude-muted transition-colors hover:bg-surface-sidebar hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised"
              aria-label="Close dialog"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </DialogPrimitive.Close>
        </div>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}
