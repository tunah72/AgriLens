"use client";

import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { useLanguage } from "../../lib/i18n";

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col items-center justify-center p-6 border border-danger-500/10 bg-danger-50 dark:bg-danger-500/10 text-danger-700 dark:text-danger-400 rounded-xl space-y-4 text-center max-w-md mx-auto animate-in fade-in duration-200">
      <div className="p-3 rounded-full bg-danger-50 dark:bg-danger-500/20 text-danger-500">
        <AlertCircle className="w-6 h-6" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-bold text-danger-700 dark:text-danger-400">{t("systemErrorOccurred")}</p>
        <p className="text-xs text-danger-500/90 dark:text-danger-400/80 leading-relaxed font-medium">{message}</p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-danger-700 dark:text-danger-400 bg-surface-raised border border-danger-500/20 hover:bg-danger-50 dark:hover:bg-danger-950/20 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-danger-500"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          {t("retryAction")}
        </button>
      )}
    </div>
  );
}
