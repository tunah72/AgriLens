"use client";

import React from "react";
import { Info } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 space-y-3 text-center border border-dashed border-surface-border bg-surface-raised rounded-xl">
      <div className="p-3 rounded-full bg-surface-sidebar text-claude-muted">
        <Info className="w-6 h-6" />
      </div>
      {action}
      <div>
        <p className="text-sm font-semibold text-claude-text">{title}</p>
        {description && (
          <p className="text-xs text-claude-muted mt-1 max-w-sm mx-auto leading-relaxed">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
