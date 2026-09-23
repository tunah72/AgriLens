"use client";

import React, { useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { fetchKnowledgeDetail, DiseaseRecommendation } from "../lib/api";
import LoadingSpinner from "./ui/LoadingSpinner";
import ErrorMessage from "./ui/ErrorMessage";
import RecommendationCard from "./RecommendationCard";
import { useLanguage } from "../lib/i18n";

interface KnowledgeDetailProps {
  diseaseLabel: string;
  onBack: () => void;
}

export default function KnowledgeDetail({ diseaseLabel, onBack }: KnowledgeDetailProps) {
  const { t } = useLanguage();
  const [disease, setDisease] = useState<DiseaseRecommendation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDiseaseDetail = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchKnowledgeDetail(diseaseLabel);
      setDisease(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("knowledgeDetailError"));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDiseaseDetail();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [diseaseLabel]);

  if (isLoading) {
    return (
      <div className="bg-surface-raised border border-surface-border rounded-2xl p-8 shadow-sm animate-pulse">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-claude-text bg-surface-raised border border-surface-border rounded-xl hover:bg-interactive-hover transition-all shadow-sm focus:outline-none"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          {t("backToList")}
        </button>
        <ErrorMessage message={error} onRetry={loadDiseaseDetail} />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={onBack}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-claude-text bg-surface-raised border border-surface-border rounded-xl hover:bg-interactive-hover transition-all shadow-sm focus:outline-none"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        {t("backToList")}
      </button>

      {disease && <RecommendationCard recommendation={disease} />}
    </div>
  );
}
