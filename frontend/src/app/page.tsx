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
  const { t } = useLanguage();
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
  const selectedImageUrl = useObjectUrl(selectedFile);

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
                    <BentoGrid className="grid-cols-1 md:grid-cols-3 md:auto-rows-[auto]">
                      
                      {/* Original Image Cell */}
                      <StaggerItem className="col-span-1 md:col-span-1">
                        <div className="glass-panel p-6 rounded-2xl h-full flex flex-col premium-shadow">
                          <h3 className="text-sm font-display font-bold uppercase tracking-widest text-claude-muted mb-4">
                            {t("uploadedImage")}
                          </h3>
                          {selectedFile && (
                            <div className="relative rounded-xl overflow-hidden flex-1 min-h-[240px] bg-surface-raised border border-surface-border">
                              {/* eslint-disable-next-line @next/next/no-img-element */}
                              <img
                                src={selectedImageUrl ?? undefined}
                                alt="Uploaded leaf image for diagnosis"
                                className="w-full h-full object-cover absolute inset-0"
                              />
                            </div>
                          )}
                          {!isSubmitting && (
                            <div className="mt-4 pt-4 border-t border-surface-border">
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
                      <StaggerItem className="col-span-1 md:col-span-2 space-y-4">
                        {isSubmitting ? (
                          <div className="glass-panel rounded-2xl p-12 flex flex-col items-center justify-center gap-4 h-full premium-shadow">
                            <LoadingSpinner />
                            <p className="text-lg font-display font-medium text-foreground">{t("analyzingImage")}</p>
                          </div>
                        ) : (
                          prediction && (
                            <div className="flex flex-col gap-4 h-full">
                              <div className="glass-panel rounded-2xl p-6 premium-shadow">
                                <h3 className="text-sm font-display font-bold uppercase tracking-widest text-claude-muted mb-4">
                                  {t("analysisResults")}
                                </h3>
                                <PredictionResult prediction={prediction} />
                              </div>
                              <div className="glass-panel rounded-2xl p-6 premium-shadow">
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
                        <StaggerItem className="col-span-1 md:col-span-3 mt-4">
                          <div className="glass-panel rounded-2xl p-6 premium-shadow">
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
