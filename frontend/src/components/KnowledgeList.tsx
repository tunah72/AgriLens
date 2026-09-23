"use client";

import React, { useEffect, useState } from "react";
import { fetchKnowledgeList, DiseaseRecommendation } from "../lib/api";
import LoadingSpinner from "./ui/LoadingSpinner";
import ErrorMessage from "./ui/ErrorMessage";
import EmptyState from "./ui/EmptyState";
import { BookOpen } from "lucide-react";
import { BentoGrid, BentoGridItem } from "./layout/BentoGrid";

interface KnowledgeListProps {
  onSelectDisease: (label: string) => void;
}

export default function KnowledgeList({ onSelectDisease }: KnowledgeListProps) {
  const [diseases, setDiseases] = useState<DiseaseRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadKnowledgeList = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetchKnowledgeList();
      setDiseases(res.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect to the knowledge base.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadKnowledgeList();
  }, []);

  if (isLoading) {
    return (
      <div className="bg-background/50 border border-surface-border rounded-3xl p-12 flex items-center justify-center shadow-sm min-h-[400px]">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorMessage
        message={error}
        onRetry={loadKnowledgeList}
      />
    );
  }

  if (diseases.length === 0) {
    return (
      <EmptyState
        title="Knowledge Base is empty"
        description="No plant disease records found in the knowledge base."
      />
    );
  }

  return (
    <div className="space-y-6">
      <BentoGrid className="md:auto-rows-[16rem]">
        {diseases.map((disease) => {
          const { label, name_vi, name_en, crop, severity, description } = disease;
          
          return (
            <button
              type="button"
              key={label}
              onClick={() => label && onSelectDisease(label)}
              className="row-span-1 w-full rounded-2xl group text-left hover:shadow-2xl transition duration-300 p-6 bg-background/50 dark:bg-black/20 border border-surface-border cursor-pointer flex flex-col justify-between overflow-hidden relative focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-claude-orange/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative z-10 space-y-2">
                <div className="flex justify-between items-start gap-2">
                  <h4 className="font-display font-bold text-foreground text-xl leading-snug group-hover:text-claude-orange transition-colors">
                    {name_en || name_vi}
                  </h4>
                </div>
                {name_vi && name_en && (
                  <p className="text-sm font-sans text-claude-muted italic">{name_vi}</p>
                )}
                {description && (
                  <p className="text-sm text-claude-muted line-clamp-2 mt-2 leading-relaxed">
                    {description}
                  </p>
                )}
              </div>

              <div className="relative z-10 flex gap-2 pt-4 border-t border-surface-border/50">
                <span className="text-xs px-2.5 py-1 bg-surface-raised border border-surface-border text-foreground font-semibold rounded-md shadow-sm">
                  {crop === "rice" ? "Rice" : crop === "coffee" ? "Coffee" : crop}
                </span>
                {severity && (
                  <span className={`text-xs px-2.5 py-1 font-semibold rounded-md border shadow-sm ${
                    severity.toLowerCase() === "high" || severity.toLowerCase() === "severe"
                      ? "bg-danger-50 text-danger-700 border-danger-500/20 dark:bg-danger-900/20 dark:text-danger-400"
                      : severity.toLowerCase() === "medium" || severity.toLowerCase() === "moderate"
                      ? "bg-warning-50 text-warning-700 border-warning-500/20 dark:bg-warning-900/20 dark:text-warning-400"
                      : "bg-healthy-50 text-healthy-700 border-healthy-500/20 dark:bg-healthy-900/20 dark:text-healthy-400"
                  }`}>
                    {severity === "high" || severity === "severe" ? "High" : severity === "medium" || severity === "moderate" ? "Medium" : "Low"}
                  </span>
                )}
              </div>
            </button>
          );
        })}
      </BentoGrid>
    </div>
  );
}
