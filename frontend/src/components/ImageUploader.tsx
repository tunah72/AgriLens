"use client";

import React, { useRef, useState } from "react";
import { Camera, X, Paperclip, Send, Image as ImageIcon } from "lucide-react";
import { ALLOWED_IMAGE_TYPES, MAX_FILE_SIZE_BYTES } from "../lib/constants";
import { useObjectUrl } from "../hooks/useObjectUrl";
import { useLanguage } from "../lib/i18n";

interface ImageUploaderProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null, validationError: string | null) => void;
  isSubmitting: boolean;
  onSubmit: () => void;
  error: string | null;
}

export default function ImageUploader({
  selectedFile,
  onFileSelect,
  isSubmitting,
  onSubmit,
  error,
}: ImageUploaderProps) {
  const { t } = useLanguage();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const validateAndSelectFile = (file: File | null) => {
    if (!file) {
      onFileSelect(null, null);
      return;
    }

    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      onFileSelect(null, t("unsupportedFormat"));
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      onFileSelect(null, t("fileTooLarge"));
      return;
    }

    onFileSelect(file, null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    validateAndSelectFile(file);
    if (e.target) e.target.value = "";
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const file = e.dataTransfer.files?.[0] || null;
    validateAndSelectFile(file);
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  const triggerCameraSelect = () => {
    cameraInputRef.current?.click();
  };

  const handleReset = (e: React.MouseEvent) => {
    e.stopPropagation();
    onFileSelect(null, null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const previewUrl = useObjectUrl(selectedFile);

  return (
    <div className="w-full space-y-3">
      {/* Prompt Bar Area */}
      <div
        className={`relative flex flex-col bg-background/50 dark:bg-black/20 border border-surface-border rounded-2xl shadow-sm transition-all duration-300 p-4 focus-within:border-claude-orange focus-within:ring-2 focus-within:ring-claude-orange/20 ${
          isDragActive ? "border-claude-orange bg-claude-orange/5 dark:bg-claude-orange/10 scale-[1.02]" : "hover:border-zinc-300 dark:hover:border-zinc-600"
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        {/* Attachment Thumbnail Previews */}
        {selectedFile && previewUrl && (
          <div className="flex items-center gap-4 bg-surface dark:bg-zinc-800/50 border border-surface-border p-3 rounded-xl w-full mb-3 animate-in fade-in zoom-in-95 duration-300">
            <div className="relative w-14 h-14 rounded-lg overflow-hidden border border-surface-border bg-black/5 flex-shrink-0">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Selected leaf image for diagnosis"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex-1 min-w-0 pr-2">
              <p className="text-sm font-semibold text-foreground truncate" title={selectedFile.name}>
                {selectedFile.name}
              </p>
              <p className="text-xs text-claude-muted font-medium mt-0.5">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            <button
              type="button"
              onClick={handleReset}
              className="p-2 rounded-full hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 transition-colors"
              aria-label={t("removeFile")}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Text Input area (styled placeholder) */}
        <div className="flex-1">
          {!selectedFile ? (
            <div 
              onClick={triggerFileSelect}
              className="w-full text-center sm:text-left text-sm text-claude-muted py-4 px-2 cursor-pointer font-medium select-none flex flex-col sm:flex-row items-center gap-2"
            >
              <ImageIcon className="w-5 h-5 opacity-50" />
              {t("dragDropPrompt")}
            </div>
          ) : (
            <div className="w-full text-center sm:text-left text-sm text-foreground py-3 px-2 font-medium">
              {t("readyToDiagnose")}
            </div>
          )}
        </div>

        {/* Action Row */}
        <div className="flex items-center justify-between border-t border-surface-border/50 pt-2.5 mt-1">
          <div className="flex items-center gap-1">
            {/* Attachment buttons */}
            <button
              type="button"
              onClick={triggerFileSelect}
              className="p-1.5 rounded-lg text-claude-muted hover:text-claude-text hover:bg-interactive-hover dark:hover:bg-stone-800 transition-all"
              title={t("attachDevice")}
              aria-label={t("attachDevice")}
            >
              <Paperclip className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={triggerCameraSelect}
              className="p-1.5 rounded-lg text-claude-muted hover:text-claude-text hover:bg-interactive-hover dark:hover:bg-stone-800 transition-all"
              title={t("takePhoto")}
              aria-label={t("takePhoto")}
            >
              <Camera className="w-4 h-4" />
            </button>
          </div>

          {/* Submit button */}
          <button
            type="button"
            onClick={onSubmit}
            disabled={isSubmitting || !selectedFile}
            className={`p-2 rounded-xl shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-claude-orange/20 ${
              isSubmitting
                ? "bg-stone-300 dark:bg-stone-700 cursor-not-allowed text-stone-500"
                : selectedFile
                ? "bg-claude-orange hover:bg-claude-orange-hover text-claude-orange-text"
                : "bg-stone-200 dark:bg-stone-800 text-stone-400 dark:text-stone-600 cursor-not-allowed"
            }`}
            title={t("startDiagnosisBtn")}
            aria-label={t("startDiagnosisBtn")}
          >
            {isSubmitting ? (
              <span className="w-4 h-4 block border-2 border-claude-orange-text/30 border-t-claude-orange-text rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Hidden inputs */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="hidden"
          onChange={handleFileChange}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          capture="environment"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {/* Errors */}
      {error && (
        <div className="p-3 border border-danger-500/10 bg-danger-50 dark:bg-danger-500/10 text-danger-700 dark:text-danger-400 rounded-xl text-xs font-medium flex gap-2 items-start animate-in fade-in duration-200">
          <span className="font-bold flex-shrink-0">{t("errorPrefix")}</span>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
