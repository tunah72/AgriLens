"use client";

import React, { useCallback, useEffect, useState } from "react";
import { Calendar, ChevronRight, FileText, LogIn } from "lucide-react";
import { fetchHistory, HistoryItem } from "../lib/api";
import LoadingSpinner from "./ui/LoadingSpinner";
import ErrorMessage from "./ui/ErrorMessage";
import EmptyState from "./ui/EmptyState";
import Pagination from "./ui/Pagination";
import RecommendationCard from "./RecommendationCard";
import { useLanguage } from "../lib/i18n";
import { DISEASE_LABELS_VI, DISEASE_LABELS_EN } from "../lib/disease-labels";

interface HistoryListProps {
  token: string | null;
  onLoginPrompt: () => void;
  onStartDiagnosis: () => void;
}

const PAGE_SIZE = 5;

export default function HistoryList({ token, onLoginPrompt, onStartDiagnosis }: HistoryListProps) {
  const { lang, t } = useLanguage();
  const [historyItems, setHistoryItems] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);

  const loadHistory = useCallback(async (targetPage: number) => {
    if (!token) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchHistory(token, targetPage, PAGE_SIZE);
      setHistoryItems(response.items || []);
      setTotal(response.total || 0);
      setPage(response.page || targetPage);
      setExpandedItemId(null);
      setHasLoaded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("historyLoadError"));
    } finally {
      setIsLoading(false);
    }
  }, [token, t]);

  useEffect(() => {
    if (token) {
      void loadHistory(1);
      return;
    }

    setHistoryItems([]);
    setTotal(0);
    setPage(1);
    setHasLoaded(false);
    setError(null);
  }, [token, loadHistory]);

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString(lang === "vi" ? "vi-VN" : "en-US", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  if (!token) {
    return (
      <div className="flex flex-col items-center justify-center space-y-6 rounded-3xl border border-surface-border bg-background/50 px-6 py-20 text-center shadow-sm dark:bg-black/20">
        <div className="rounded-full bg-claude-orange/10 p-5 text-claude-orange shadow-inner">
          <LogIn className="h-8 w-8" aria-hidden="true" />
        </div>
        <div className="space-y-2">
          <p className="text-xl font-display font-bold text-foreground">{t("signInPromptTitle")}</p>
          <p className="mx-auto max-w-sm text-sm font-sans leading-relaxed text-claude-muted">
            {t("signInPromptDesc")}
          </p>
        </div>
        <button
          type="button"
          onClick={onLoginPrompt}
          className="inline-flex min-h-11 items-center gap-1.5 rounded-lg bg-claude-orange px-4 py-2.5 text-xs font-semibold text-claude-orange-text shadow-sm transition-colors hover:bg-claude-orange-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2"
        >
          {t("signInNow")}
        </button>
      </div>
    );
  }

  if (isLoading && !hasLoaded) {
    return (
      <div className="flex items-center justify-center rounded-2xl border border-surface-border bg-surface-raised p-8 shadow-sm">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={() => void loadHistory(page)} />;
  }

  if (historyItems.length === 0) {
    return (
      <EmptyState
        title={t("emptyHistoryTitle")}
        description={t("emptyHistoryDesc")}
        action={
          <button
            type="button"
            onClick={onStartDiagnosis}
            className="min-h-11 rounded-lg bg-claude-orange px-4 py-2 text-sm font-semibold text-claude-orange-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2"
          >
            {t("newDiagnosis")}
          </button>
        }
      />
    );
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-wider text-claude-muted">
          {t("allDiagnoses")} ({total})
        </p>
      </div>

      <div className="space-y-3" aria-busy={isLoading}>
        {historyItems.map((item) => {
          const isExpanded = expandedItemId === item.id;
          const diseaseName =
            lang === "vi"
              ? (item.recommendation?.name_vi || item.recommendation?.name_en || DISEASE_LABELS_VI[item.predicted_label] || item.predicted_label)
              : (item.recommendation?.name_en || item.recommendation?.name_vi || DISEASE_LABELS_EN[item.predicted_label] || item.predicted_label);
          const crop = item.recommendation?.crop;
          const cropDisplay =
            crop === "rice"
              ? t("cropRice")
              : crop === "coffee"
              ? t("cropCoffee")
              : crop;

          return (
            <div
              key={item.id}
              className="overflow-hidden rounded-2xl border border-surface-border bg-background/50 shadow-sm transition-shadow duration-300 hover:shadow-md dark:bg-black/20"
            >
              <button
                type="button"
                onClick={() => setExpandedItemId(isExpanded ? null : item.id)}
                aria-expanded={isExpanded}
                aria-controls={`history-detail-${item.id}`}
                className="flex w-full items-center justify-between gap-4 p-5 text-left transition-colors hover:bg-surface-sidebar focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-inset dark:hover:bg-zinc-800/50"
              >
                <div className="flex min-w-0 items-center gap-3.5">
                  {item.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={item.image_url}
                      alt="Leaf image from diagnosis history"
                      className="h-12 w-12 shrink-0 rounded-lg border border-surface-border bg-surface-raised object-cover"
                    />
                  ) : (
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-surface-border bg-surface-raised text-claude-muted">
                      <FileText className="h-5 w-5" aria-hidden="true" />
                    </div>
                  )}
                  <div className="min-w-0">
                    <h4 className="truncate text-base font-display font-bold text-foreground">{diseaseName}</h4>
                    <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-medium text-claude-muted">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" aria-hidden="true" />
                        {formatDate(item.created_at)}
                      </span>
                      {crop && (
                        <span className="rounded bg-surface-border/50 px-2 py-0.5 text-[10px] font-semibold text-foreground">
                          {cropDisplay}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="text-xl font-display font-bold text-claude-orange">{Math.round(item.confidence * 100)}%</div>
                    <div className="mt-0.5 text-[10px] font-medium uppercase tracking-wider text-claude-muted">
                      {t("confidenceScores")}
                    </div>
                  </div>
                  <span className="inline-flex h-11 w-11 items-center justify-center rounded-full text-claude-muted" aria-hidden="true">
                    <ChevronRight className={`h-4 w-4 transition-transform duration-200 ${isExpanded ? "rotate-90" : ""}`} aria-hidden="true" />
                  </span>
                </div>
              </button>

              {isExpanded && (
                <div id={`history-detail-${item.id}`} className="border-t border-surface-border bg-background/30 p-5 dark:bg-black/10">
                  <RecommendationCard recommendation={item.recommendation} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <Pagination
        page={page}
        totalPages={totalPages}
        isLoading={isLoading}
        onPageChange={(targetPage) => void loadHistory(targetPage)}
      />
    </div>
  );
}
