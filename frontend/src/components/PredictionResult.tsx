"use client";

import React from "react";
import { PredictionResponse } from "../lib/api";
import { motion } from "framer-motion";
import { getDiseaseDisplayName } from "../lib/disease-labels";
import { useLanguage } from "../lib/i18n";
import { AlertTriangle, Lightbulb, Target } from "lucide-react";

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
  const secondaryName =
    rawLabel === "Healthy"
      ? t("healthyStatusNote")
      : lang === "vi"
      ? diseaseNameEn
      : diseaseNameVi;

  const confidencePercent = Math.round(confidence * 100);
  const confidencePercentDetailed = (confidence * 100).toFixed(1);
  const localizedConfidenceNote =
    confidence < 0.6
      ? t("confidenceLowNote", { conf: confidencePercentDetailed })
      : t("confidenceGoodNote", { conf: confidencePercentDetailed });

  const cropDisplay =
    recommendation?.crop === "rice"
      ? t("cropRice")
      : recommendation?.crop === "coffee"
      ? t("cropCoffee")
      : recommendation?.crop === "rice/coffee" || recommendation?.crop === "coffee/rice"
      ? t("cropRiceCoffee")
      : recommendation?.crop;

  const severityDisplay =
    recommendation?.severity?.toLowerCase() === "high" || recommendation?.severity?.toLowerCase() === "severe"
      ? t("severityHigh")
      : recommendation?.severity?.toLowerCase() === "medium" || recommendation?.severity?.toLowerCase() === "moderate"
      ? t("severityMedium")
      : t("severityLow");

  if (prediction.is_valid_leaf === false || rawLabel === "InvalidLeaf") {
    const defaultWarningVi =
      "Hình ảnh có đặc điểm của tài liệu, văn bản hoặc giấy tờ, không phải lá cây lúa hoặc cà phê.";
    const defaultWarningEn =
      "Image characteristics match a document, text, or paper sheet, not a rice or coffee leaf.";

    const warningText =
      lang === "vi"
        ? (prediction.domain_warning || defaultWarningVi)
        : (prediction.domain_warning_en || defaultWarningEn);

    return (
      <div className="w-full space-y-6">
        <div className="flex flex-col gap-2 border-b border-warning-500/20 pb-5">
          <span className="text-xs font-display font-bold uppercase tracking-[0.2em] text-warning-500 font-semibold">
            {lang === "vi" ? "Ngoài phạm vi chẩn đoán (Out-of-Domain)" : "Out of Domain"}
          </span>
          <h3 className="text-2xl sm:text-3xl font-display font-bold text-foreground leading-tight mt-1">
            {lang === "vi" ? "Không phải phiến lá hợp lệ" : "Invalid Leaf Specimen"}
          </h3>
          <p className="text-sm font-sans text-claude-muted mt-1 leading-relaxed">
            {warningText}
          </p>
        </div>

        <div className="p-5 bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 rounded-2xl text-sm space-y-3 shadow-sm">
          <div className="flex items-center gap-2 font-bold text-base text-amber-700 dark:text-amber-300">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{lang === "vi" ? "Hướng dẫn chụp ảnh chuẩn xác" : "Image Capture Guidelines"}</span>
          </div>
          <ul className="list-disc list-inside space-y-2 text-xs sm:text-sm text-foreground/90 leading-relaxed">
            <li>{lang === "vi" ? "Chụp cận cảnh phiến lá lúa hoặc lá cà phê còn tươi trên cây." : "Capture a clear close-up of a fresh rice or coffee leaf."}</li>
            <li>{lang === "vi" ? "Tránh chụp văn bản, bằng khen, hóa đơn, màn hình, hoa quả hoặc vật thể lạ." : "Avoid capturing documents, certificates, screens, flowers, or arbitrary objects."}</li>
            <li>{lang === "vi" ? "Đảm bảo đủ ánh sáng tự nhiên và lấy nét rõ vào bề mặt phiến lá." : "Ensure natural lighting and sharp focus on the leaf surface."}</li>
          </ul>
        </div>
      </div>
    );
  }

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
      {prediction.detections && prediction.detections.length > 0 && (
        <div className="p-4 rounded-2xl border border-surface-border bg-background/50 dark:bg-black/20 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-display font-medium uppercase tracking-wider text-claude-muted flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5 shrink-0" />
              <span>{t("detectedLesions")}</span>
            </span>
            <span className="px-2.5 py-0.5 text-xs font-bold bg-claude-orange/10 text-claude-orange border border-claude-orange/20 rounded-full">
              {prediction.detections.length}{" "}
              {lang === "vi"
                ? "vùng tổn thương"
                : prediction.detections.length === 1
                ? "lesion spot"
                : "lesion spots"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
            {prediction.detections.map((det, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-xl bg-surface-raised/70 border border-surface-border/60 text-xs"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-2.5 h-2.5 rounded-full bg-claude-orange shrink-0 shadow-sm" />
                  <span className="font-semibold text-foreground truncate">
                    {getDiseaseDisplayName(det.label, lang)}
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {det.area_pct !== undefined && det.area_pct > 0 && (
                    <span className="text-claude-muted font-medium">
                      {det.area_pct.toFixed(1)}% {lang === "vi" ? "diện tích" : "area"}
                    </span>
                  )}
                  <span className="font-bold text-claude-orange">
                    {Math.round(det.confidence * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {localizedConfidenceNote && (
        <div className="p-4 bg-warning-50 dark:bg-warning-900/10 border border-warning-500/20 text-warning-800 dark:text-warning-400 rounded-2xl text-sm font-medium flex gap-3 items-start shadow-sm">
          <Lightbulb className="w-5 h-5 shrink-0 text-amber-500 mt-0.5" />
          <span className="pt-0.5">{localizedConfidenceNote}</span>
        </div>
      )}
    </div>
  );
}
