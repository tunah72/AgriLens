"use client";

import React, { useState } from "react";
import ImageUploader from "../components/ImageUploader";
import PredictionResult from "../components/PredictionResult";
import TopKList from "../components/TopKList";
import RecommendationCard from "../components/RecommendationCard";
import LoadingSpinner from "../components/ui/LoadingSpinner";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";
import AuthModal from "../components/AuthModal";
import KnowledgeList from "../components/KnowledgeList";
import KnowledgeDetail from "../components/KnowledgeDetail";
import HistoryList from "../components/HistoryList";
import { usePrediction } from "../hooks/usePrediction";
import { useAuth } from "../hooks/useAuth";
import { TabId } from "../components/TabNav";
import { useObjectUrl } from "../hooks/useObjectUrl";
import { BentoGrid } from "../components/layout/BentoGrid";
import { FadeIn, SlideUp, StaggerContainer, StaggerItem } from "../components/animations/Animations";
import { useLanguage } from "../lib/i18n";

export default function Home() {
  const { lang, t } = useLanguage();
  const auth = useAuth();
  const {
    selectedFile,
    prediction,
    error,
    isSubmitting,
    handleFileSelect,
    handleSubmit,
    handleReset,
  } = usePrediction();

  const [activeTab, setActiveTab] = useState<TabId>("diagnosis");
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [selectedDisease, setSelectedDisease] = useState<string | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const authTriggerRef = React.useRef<HTMLElement | null>(null);
  const mainContentRef = React.useRef<HTMLElement | null>(null);
  
  const [theme, setTheme] = React.useState<"light" | "dark">("light");
  const [viewAnnotated, setViewAnnotated] = useState(true);
  const selectedImageUrl = useObjectUrl(selectedFile);

  React.useEffect(() => {
    if (prediction?.annotated_image_url) {
      setViewAnnotated(true);
    }
  }, [prediction]);
  React.useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark") || 
                   localStorage.getItem("theme") === "dark";
    setTheme(isDark ? "dark" : "light");
    if (isDark) {
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const handlePredictSubmit = () => {
    handleSubmit(auth.token || undefined);
  };

  const startNewDiagnosis = React.useCallback(() => {
    if (isSubmitting) return;

    handleReset();
    setSelectedDisease(null);
    setActiveTab("diagnosis");
  }, [handleReset, isSubmitting]);

  React.useEffect(() => {
    if (auth.sessionMessage) setIsAuthModalOpen(true);
  }, [auth.sessionMessage]);

  const closeAuthModal = React.useCallback(() => {
    setIsAuthModalOpen(false);
    auth.clearSessionMessage();
  }, [auth]);

  const openAuthModal = React.useCallback(() => {
    authTriggerRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setIsAuthModalOpen(true);
  }, []);

  const getActiveTabLabel = () => {
    switch (activeTab) {
      case "diagnosis":
        return t("diagnosis");
      case "knowledge":
        return t("knowledge");
      case "history":
        return t("history");
      default:
        return t("diagnosis");
    }
  };

  return (
    <div className={`min-h-screen bg-background flex flex-col lg:flex-row ${theme === "dark" ? "dark" : ""}`}>
      {/* Sidebar navigation */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        onNewDiagnosis={startNewDiagnosis}
        user={auth.user}
        isLoading={auth.isLoading}
        isPredictionSubmitting={isSubmitting}
        logout={auth.logout}
        onLoginClick={openAuthModal}
        isCollapsed={isSidebarCollapsed}
        onCollapsedChange={setIsSidebarCollapsed}
      />

      {/* Main layout container */}
      <div className={`flex-1 flex flex-col min-w-0 pb-16 lg:pb-0 min-h-screen transition-[padding] duration-300 ${isSidebarCollapsed ? "lg:pl-[72px]" : "lg:pl-64"}`}>
        <Header 
          activeTabLabel={getActiveTabLabel()} 
          theme={theme}
          onThemeToggle={toggleTheme}
        />

        <main ref={mainContentRef} tabIndex={-1} className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-6xl mx-auto w-full">
            
            {activeTab === "diagnosis" && (
              <StaggerContainer className="flex flex-col gap-8 pb-10">
                {!prediction && !isSubmitting ? (
                  <StaggerItem>
                    <div className="flex flex-col items-center justify-center text-center py-12 md:py-20">
                      <h2 className="text-4xl sm:text-5xl md:text-6xl font-display font-bold text-foreground tracking-tight leading-[1.15]">
                        {t("heroTitle")}
                      </h2>
                      <p className="mt-4 text-claude-muted font-sans max-w-lg leading-relaxed">
                        {t("heroSubtitle")}
                      </p>
                      <div className="w-full max-w-2xl mt-10">
                        <div className="glass-panel rounded-3xl p-6 sm:p-8 premium-shadow">
                          <ImageUploader
                            onSubmit={handlePredictSubmit}
                            onFileSelect={handleFileSelect}
                            selectedFile={selectedFile}
                            isSubmitting={isSubmitting}
                            error={error}
                          />
                        </div>
                      </div>
                    </div>
                  </StaggerItem>
                ) : (
                  <StaggerContainer className="w-full">
                    <BentoGrid className="grid-cols-1 lg:grid-cols-12 md:auto-rows-[auto] gap-6 max-w-7xl mx-auto">
                      
                      {/* Original / Annotated Image Cell */}
                      <StaggerItem className="col-span-1 lg:col-span-5">
                        <div className="glass-panel p-6 sm:p-7 rounded-3xl h-full flex flex-col premium-shadow space-y-4">
                          <div className="flex items-center justify-between gap-3 pb-3 border-b border-surface-border/50">
                            <div className="min-w-0">
                              <h3 className="text-xs font-display font-bold uppercase tracking-wider text-claude-orange/90 block">
                                {prediction?.annotated_image_url && viewAnnotated
                                  ? t("viewModeAnnotated")
                                  : t("uploadedImage")}
                              </h3>
                              <p className="text-xs text-claude-muted mt-0.5 truncate">
                                {prediction?.annotated_image_url && viewAnnotated
                                  ? (lang === "vi" ? "Lớp phủ mặt nạ & khung định vị đốm bệnh" : "Mask overlay & bounding box")
                                  : (lang === "vi" ? "Ảnh chụp mẫu lá ban đầu" : "Original captured specimen")}
                              </p>
                            </div>
                            {prediction?.annotated_image_url && (
                              <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold bg-claude-orange/10 text-claude-orange border border-claude-orange/20 rounded-full shrink-0">
                                YOLO26-seg
                              </span>
                            )}
                          </div>

                          {/* Dedicated Segmented Control Bar (Zero collision, perfectly responsive) */}
                          {prediction?.annotated_image_url && (
                            <div className="grid grid-cols-2 p-1 bg-surface-raised border border-surface-border rounded-xl text-xs font-semibold shadow-xs gap-1">
                              <button
                                type="button"
                                onClick={() => setViewAnnotated(false)}
                                className={`py-2 px-3 rounded-lg transition-all text-center flex items-center justify-center gap-1.5 ${
                                  !viewAnnotated
                                    ? "bg-surface font-bold text-foreground shadow-sm border border-surface-border"
                                    : "text-claude-muted hover:text-foreground hover:bg-surface/50"
                                }`}
                              >
                                <span>🍃</span>
                                <span className="truncate">{t("viewModeOriginal")}</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setViewAnnotated(true)}
                                className={`py-2 px-3 rounded-lg transition-all text-center flex items-center justify-center gap-1.5 ${
                                  viewAnnotated
                                    ? "bg-claude-orange text-white font-bold shadow-sm"
                                    : "text-claude-muted hover:text-foreground hover:bg-surface/50"
                                }`}
                              >
                                <span>🎯</span>
                                <span className="truncate">{t("viewModeAnnotated")}</span>
                              </button>
                            </div>
                          )}
                          {(selectedFile || prediction?.image_url) && (
                            <div className="relative rounded-2xl overflow-hidden w-full aspect-square max-h-[520px] bg-zinc-950/5 dark:bg-black/30 border border-surface-border flex items-center justify-center p-2 group shadow-inner">
                              {/* eslint-disable-next-line @next/next/no-img-element */}
                              <img
                                src={
                                  viewAnnotated && prediction?.annotated_image_url
                                    ? prediction.annotated_image_url
                                    : (selectedImageUrl || prediction?.image_url || undefined)
                                }
                                alt="Leaf image for diagnosis"
                                className="w-full h-full object-contain rounded-xl transition-all duration-300 drop-shadow-sm"
                              />
                            </div>
                          )}
                          {!isSubmitting && (
                            <div className="mt-2 pt-3 border-t border-surface-border/50">
                              <ImageUploader
                                selectedFile={selectedFile}
                                onFileSelect={handleFileSelect}
                                isSubmitting={isSubmitting}
                                onSubmit={handlePredictSubmit}
                                error={error}
                              />
                            </div>
                          )}
                        </div>
                      </StaggerItem>

                      {/* AI Result Cell */}
                      <StaggerItem className="col-span-1 lg:col-span-7 space-y-4">
                        {isSubmitting ? (
                          <div className="glass-panel rounded-3xl p-12 flex flex-col items-center justify-center gap-4 h-full premium-shadow">
                            <LoadingSpinner />
                            <p className="text-lg font-display font-medium text-foreground">{t("analyzingImage")}</p>
                          </div>
                        ) : (
                          prediction && (
                            <div className="flex flex-col gap-4 h-full">
                              <div className="glass-panel rounded-3xl p-6 sm:p-7 premium-shadow">
                                <h3 className="text-sm font-display font-bold uppercase tracking-widest text-claude-muted mb-4">
                                  {t("analysisResults")}
                                </h3>
                                <PredictionResult prediction={prediction} />
                              </div>
                              <div className="glass-panel rounded-3xl p-6 sm:p-7 premium-shadow">
                                <h3 className="text-sm font-display font-bold uppercase tracking-widest text-claude-muted mb-4">
                                  {t("confidenceAlternatives")}
                                </h3>
                                <TopKList topK={prediction.top_k} />
                              </div>
                            </div>
                          )
                        )}
                      </StaggerItem>

                      {/* Recommendation Cell spans full width */}
                      {!isSubmitting && prediction && (
                        <StaggerItem className="col-span-1 lg:col-span-12 mt-4">
                          <div className="glass-panel rounded-3xl p-6 sm:p-8 premium-shadow">
                             <RecommendationCard recommendation={prediction.recommendation} />
                          </div>
                        </StaggerItem>
                      )}
                    </BentoGrid>
                  </StaggerContainer>
                )}
              </StaggerContainer>
            )}

            {activeTab === "knowledge" && (
              <FadeIn className="space-y-4 pb-10">
                {selectedDisease ? (
                  <div className="glass-panel rounded-3xl p-6 premium-shadow">
                    <KnowledgeDetail
                      diseaseLabel={selectedDisease}
                      onBack={() => setSelectedDisease(null)}
                    />
                  </div>
                ) : (
                  <>
                    <h2 className="text-2xl font-display font-bold text-foreground mb-6">
                      {t("knowledgeBaseTitle")}
                    </h2>
                    <div className="glass-panel rounded-3xl p-6 premium-shadow">
                      <KnowledgeList onSelectDisease={setSelectedDisease} />
                    </div>
                  </>
                )}
              </FadeIn>
            )}

            {activeTab === "history" && (
              <SlideUp className="space-y-4 pb-10">
                <h2 className="text-2xl font-display font-bold text-foreground mb-6">
                  {t("historyTitle")}
                </h2>
                <div className="glass-panel rounded-3xl p-6 premium-shadow">
                  <HistoryList
                    token={auth.token}
                    onLoginPrompt={openAuthModal}
                    onStartDiagnosis={startNewDiagnosis}
                  />
                </div>
              </SlideUp>
            )}
            
          </div>
        </main>
      </div>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={closeAuthModal}
        auth={auth}
        sessionMessage={auth.sessionMessage}
        restoreFocusRef={authTriggerRef}
        fallbackFocusRef={mainContentRef}
      />
    </div>
  );
}
