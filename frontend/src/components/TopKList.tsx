"use client";

import React from "react";
import { TopKPrediction } from "../lib/api";
import { getDiseaseDisplayName } from "../lib/disease-labels";

interface TopKListProps {
  topK: TopKPrediction[];
}

export default function TopKList({ topK }: TopKListProps) {
  if (!topK || topK.length === 0) return null;

  const hasClosePrediction =
    topK.length >= 2 && topK[0].confidence - topK[1].confidence < 0.1;

  const maxConfidence = topK[0].confidence || 1;

  return (
    <div className="w-full p-5 bg-surface-raised border border-surface-border rounded-xl shadow-sm space-y-4">
      <div>
        <h4 className="text-sm font-semibold uppercase tracking-wider text-claude-muted">
          Alternative Diagnoses Considered
        </h4>
        <p className="text-xs text-claude-muted mt-0.5">
          Confidence scores of top ranked candidates
        </p>
      </div>

      <div className="space-y-3.5">
        {topK.map((item, index) => {
          const percentage = Math.round(item.confidence * 100);
          const barWidthPercent = Math.max(
            5,
            Math.round((item.confidence / maxConfidence) * 100)
          );

          return (
            <div key={item.label} className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-claude-text truncate">{getDiseaseDisplayName(item.label)}</span>
                <span className="text-claude-text">{percentage}%</span>
              </div>
              <div className="w-full h-2 bg-surface border border-surface-border/20 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    index === 0
                      ? "bg-healthy-500"
                      : index === 1
                      ? "bg-healthy-500/60"
                      : "bg-surface-border"
                  }`}
                  style={{ width: `${barWidthPercent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {hasClosePrediction && (
        <div className="p-3.5 bg-warning-50 dark:bg-warning-500/10 border border-warning-100/50 dark:border-warning-500/20 text-warning-700 dark:text-warning-300 rounded-lg text-xs space-y-1.5 animate-in fade-in duration-200">
          <p className="font-bold flex items-center gap-1">
            ⚠️ Close Margin Prediction
          </p>
          <p className="leading-relaxed font-medium">
            The top two predicted classes differ by less than 10%. Recommendation: Compare field symptoms against the Knowledge Base or capture clearer photos for optimal diagnosis.
          </p>
        </div>
      )}
    </div>
  );
}
