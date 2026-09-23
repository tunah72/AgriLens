"use client";

import React from "react";

export default function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 space-y-3 text-center" role="status" aria-live="polite">
      <div className="relative w-10 h-10">
        <div className="absolute top-0 left-0 w-full h-full border-4 border-surface-border rounded-full"></div>
        <div className="absolute top-0 left-0 w-full h-full border-4 border-claude-orange border-t-transparent rounded-full animate-spin"></div>
      </div>
      <p className="text-sm font-semibold text-foreground">Processing analysis...</p>
      <p className="text-xs text-claude-muted">AI model is diagnosing the leaf image</p>
    </div>
  );
}
