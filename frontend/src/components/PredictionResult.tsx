"use client";

import React from "react";
import { PredictionResponse } from "../lib/api";
import { motion } from "framer-motion";
import { getDiseaseDisplayName } from "../lib/disease-labels";
import { useLanguage } from "../lib/i18n";

interface PredictionResultProps {
  prediction: PredictionResponse;
}

export default function PredictionResult({ prediction }: PredictionResultProps) {
  const { lang, t } = useLanguage();
  const {
    prediction: rawLabel,
    confidence,
    recommendation,
    latency_ms,
  } = prediction;

  const diseaseNameVi = recommendation?.name_vi || getDiseaseDisplayName(rawLabel, "vi");
  const diseaseNameEn = recommendation?.name_en || getDiseaseDisplayName(rawLabel, "en");

  // Primary and secondary display names based on current language
  const primaryName = lang === "vi" ? diseaseNameVi : diseaseNameEn;
  const secondaryName = lang === "vi" ? diseaseNameEn : diseaseNameVi;

  const confidencePercent = Math.round(confidence * 100);
  const confidenceNote = recommendation?.confidence_note;

  const cropDisplay =
    recommendation?.crop === "rice"
      ? t("cropRice")
      : recommendation?.crop === "coffee"
      ? t("cropCoffee")
      : recommendation?.crop;

  const severityDisplay =
    recommendation?.severity?.toLowerCase() === "high" || recommendation?.severity?.toLowerCase() === "severe"
      ? t("severityHigh")
      : recommendation?.severity?.toLowerCase() === "medium" || recommendation?.severity?.toLowerCase() === "moderate"
      ? t("severityMedium")
      : t("severityLow");

  return (
    <div className="w-full space-y-6">
      <div className="flex flex-col gap-2 border-b border-surface-border/50 pb-5">
        <span className="text-xs font-display font-bold uppercase tracking-[0.2em] text-claude-orange/80">
          {t("topPrediction")}
        </span>
        <h3 className="text-3xl sm:text-4xl md:text-5xl font-display font-bold text-foreground leading-tight mt-1">
          {primaryName}
        </h3>
        {secondaryName && secondaryName !== primaryName && (
          <p className="text-sm font-sans text-claude-muted italic mt-1">
            {secondaryName}
          </p>
        )}
        <div className="mt-4 flex flex-wrap gap-2 items-center">
          {recommendation?.crop && (
            <span className="text-xs px-2.5 py-1 bg-surface-raised border border-surface-border text-claude-muted font-semibold rounded-md shadow-sm">
              {t("crop")}: {cropDisplay}
            </span>
          )}
          {recommendation?.severity && (
            <span className={`text-xs px-2.5 py-1 font-semibold rounded-md border shadow-sm ${
              recommendation.severity.toLowerCase() === "high" || recommendation.severity.toLowerCase() === "severe"
                ? "bg-danger-50 text-danger-700 border-danger-500/20 dark:bg-danger-900/20 dark:text-danger-400"
                : recommendation.severity.toLowerCase() === "medium" || recommendation.severity.toLowerCase() === "moderate"
                ? "bg-warning-50 text-warning-700 border-warning-500/20 dark:bg-warning-900/20 dark:text-warning-400"
                : "bg-healthy-50 text-healthy-700 border-healthy-500/20 dark:bg-healthy-900/20 dark:text-healthy-400"
            }`}>
              {t("severity")}: {severityDisplay}
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="flex flex-col p-4 bg-background/50 dark:bg-black/20 border border-surface-border rounded-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-claude-orange/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          <span className="text-xs text-claude-muted font-display font-medium uppercase tracking-wider relative z-10">
            {t("confidenceScores")}
          </span>
          <span className="text-4xl font-bold font-display text-claude-orange mt-2 relative z-10">
            {confidencePercent}%
          </span>
          <div className="w-full bg-surface-border/50 h-1.5 rounded-full mt-4 overflow-hidden relative z-10">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${confidencePercent}%` }}
              transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
              className="h-full bg-claude-orange rounded-full"
            />
          </div>
        </div>
        <div className="flex flex-col justify-center rounded-2xl border border-surface-border bg-background/50 p-4 dark:bg-black/20">
          <span className="text-xs font-medium uppercase tracking-wider text-claude-muted">
            {t("modelLatency")}
          </span>
          <span className="mt-2 text-2xl font-bold text-foreground">
            {latency_ms === undefined ? "N/A" : `${latency_ms.toFixed(0)} ms`}
          </span>
        </div>
      </div>

      {confidenceNote && (
        <div className="p-4 bg-warning-50 dark:bg-warning-900/10 border border-warning-500/20 text-warning-800 dark:text-warning-400 rounded-2xl text-sm font-medium flex gap-3 items-start shadow-sm">
          <span className="text-xl">💡</span>
          <span className="pt-0.5">{confidenceNote}</span>
        </div>
      )}
    </div>
  );
}
