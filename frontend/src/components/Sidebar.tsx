"use client";

import React, { useState } from "react";
import { BookOpen, ChevronLeft, ChevronRight, History, Leaf, LogIn, Plus } from "lucide-react";
import type { UserResponse } from "../lib/api";
import { TabId } from "./TabNav";
import AccountMenu from "./ui/AccountMenu";
import { useLanguage, Language } from "../lib/i18n";

interface SidebarProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  onNewDiagnosis: () => void;
  user: UserResponse | null;
  isLoading: boolean;
  isPredictionSubmitting: boolean;
  logout: () => void;
  onLoginClick: () => void;
  isCollapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  lang?: Language;
}

export default function Sidebar({
  activeTab,
  onTabChange,
  onNewDiagnosis,
  user,
  isLoading,
  isPredictionSubmitting,
  logout,
  onLoginClick,
  isCollapsed: controlledCollapsed,
  onCollapsedChange,
  lang: propLang,
}: SidebarProps) {
  const context = useLanguage();
  const t = context.t;
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledCollapsed ?? internalCollapsed;

  const toggleCollapsed = () => {
    const nextCollapsed = !isCollapsed;
    onCollapsedChange?.(nextCollapsed);
    if (controlledCollapsed === undefined) setInternalCollapsed(nextCollapsed);
  };

  const menuItems = [
    {
      id: "knowledge" as TabId,
      label: t("knowledge"),
      mobileLabel: t("knowledgeShort"),
      icon: BookOpen,
    },
    {
      id: "history" as TabId,
      label: t("history"),
      mobileLabel: t("historyShort"),
      icon: History,
    },
  ];

  return (
    <>
      {/* Mobile Bottom Navigation */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around gap-1 border-t border-surface-border bg-surface-sidebar px-2 py-2 shadow-lg lg:hidden"
        aria-label="Main navigation"
      >
        <button
          type="button"
          aria-pressed={activeTab === "diagnosis"}
          onClick={onNewDiagnosis}
          disabled={isPredictionSubmitting}
          className={`inline-flex min-h-11 min-w-11 flex-col items-center justify-center rounded-xl px-2 py-1 text-[10px] tracking-wide transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar ${
            activeTab === "diagnosis"
              ? "bg-interactive-active font-semibold text-claude-orange"
              : "text-text-secondary hover:text-claude-text"
          }`}
        >
          <Plus className="mb-0.5 h-5 w-5" aria-hidden="true" />
          <span>{t("diagnosis")}</span>
        </button>

        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              type="button"
              aria-pressed={isActive}
              onClick={() => onTabChange(item.id)}
              className={`inline-flex min-h-11 min-w-11 flex-col items-center justify-center rounded-xl px-2 py-1 text-[10px] tracking-wide transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar ${
                isActive
                  ? "bg-interactive-active font-semibold text-claude-orange"
                  : "text-text-secondary hover:text-claude-text"
              }`}
            >
              <Icon className="mb-0.5 h-5 w-5" aria-hidden="true" />
              <span>{item.mobileLabel}</span>
            </button>
          );
        })}

        {isLoading ? (
          <div className="flex h-11 w-11 items-center justify-center text-claude-muted" role="status" aria-label={t("loadingAccount")}>
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-claude-orange/30 border-t-claude-orange" aria-hidden="true" />
          </div>
        ) : user ? (
          <AccountMenu username={user.username} onLogout={logout} variant="mobile" />
        ) : (
          <button
            type="button"
            onClick={onLoginClick}
            className="inline-flex h-11 w-11 flex-col items-center justify-center rounded-xl border border-surface-border bg-surface-raised text-text-secondary shadow-sm transition-colors hover:bg-surface-sidebar hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar"
            aria-label={t("signIn")}
          >
            <LogIn className="h-5 w-5" aria-hidden="true" />
          </button>
        )}
      </nav>

      {/* Desktop Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-30 hidden h-screen flex-col border-r border-surface-border bg-surface-sidebar transition-[width] duration-300 lg:flex ${
          isCollapsed ? "w-[72px]" : "w-64"
        }`}
        aria-label="Sidebar navigation"
      >
        <div className={`flex h-16 items-center border-b border-surface-border/50 ${isCollapsed ? "justify-center px-3" : "justify-between px-4"}`}>
          {!isCollapsed ? (
            <>
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-claude-orange/10 text-claude-orange border border-claude-orange/20 shadow-xs">
                  <Leaf className="h-5 w-5 fill-claude-orange/20" aria-hidden="true" />
                </div>
                <span className="text-xl font-serif font-bold tracking-tight text-foreground truncate">{t("brand")}</span>
              </div>
              <button
                type="button"
                onClick={toggleCollapsed}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-surface-border/60 bg-surface-raised/70 text-text-secondary transition-all hover:bg-surface-hover hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange"
                aria-label={t("collapseNav")}
                title={t("collapseNav")}
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={toggleCollapsed}
              className="group relative flex h-11 w-11 items-center justify-center rounded-xl border border-surface-border bg-surface-raised text-claude-orange shadow-xs transition-all hover:bg-surface-hover hover:border-claude-orange/40 hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar"
              aria-label={t("expandNav")}
              title={t("expandNav")}
            >
              <Leaf className="h-5 w-5 text-claude-orange transition-all duration-200 group-hover:scale-0 group-hover:opacity-0" aria-hidden="true" />
              <ChevronRight className="h-5 w-5 text-claude-orange absolute scale-0 opacity-0 transition-all duration-200 group-hover:scale-100 group-hover:opacity-100" aria-hidden="true" />
            </button>
          )}
        </div>

        <div className="my-3 px-3">
          <button
            type="button"
            onClick={onNewDiagnosis}
            disabled={isPredictionSubmitting}
            className={`flex w-full min-h-11 items-center justify-center rounded-xl border border-surface-border bg-surface-raised font-medium shadow-xs transition-all hover:bg-surface-hover hover:border-claude-orange/40 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange ${
              isCollapsed ? "h-11 w-11 mx-auto p-0" : "px-3 py-2 gap-2 text-sm"
            } ${activeTab === "diagnosis" ? "border-claude-orange/60 ring-2 ring-claude-orange/20" : ""}`}
            title={t("newDiagnosis")}
          >
            <Plus className="h-5 w-5 shrink-0 text-claude-orange" aria-hidden="true" />
            {!isCollapsed && <span className="text-foreground">{t("newDiagnosis")}</span>}
          </button>
        </div>

        <nav className="flex-1 space-y-1.5 px-3" aria-label="Navigation items">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                type="button"
                aria-pressed={isActive}
                onClick={() => onTabChange(item.id)}
                className={`flex min-h-11 w-full items-center rounded-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange ${
                  isCollapsed ? "h-11 w-11 mx-auto justify-center p-0" : "gap-3 px-3 py-2 text-left"
                } ${
                  isActive
                    ? "bg-interactive-active font-semibold text-claude-orange shadow-xs border border-claude-orange/20"
                    : "text-text-secondary hover:bg-interactive-hover hover:text-claude-text"
                }`}
                title={isCollapsed ? item.label : undefined}
                aria-label={isCollapsed ? item.label : undefined}
              >
                <Icon className={`h-5 w-5 shrink-0 ${isActive ? "text-claude-orange" : "text-text-secondary"}`} aria-hidden="true" />
                {!isCollapsed && <span className="text-sm font-medium leading-none">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-surface-border/50 p-3">
          {isLoading ? (
            <div className="flex min-h-11 items-center justify-center text-claude-muted" role="status" aria-label={t("loadingAccount")}>
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-claude-orange/30 border-t-claude-orange" aria-hidden="true" />
            </div>
          ) : user ? (
            <AccountMenu username={user.username} onLogout={logout} variant={isCollapsed ? "mobile" : "sidebar"} />
          ) : (
            <button
              type="button"
              onClick={onLoginClick}
              className={`flex min-h-11 w-full items-center justify-center rounded-xl border border-surface-border bg-surface-raised shadow-xs transition-all hover:bg-surface-hover hover:border-claude-orange/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange ${
                isCollapsed ? "h-11 w-11 mx-auto p-0" : "gap-2 px-3 py-2 text-xs font-semibold"
              }`}
              title={t("signIn")}
              aria-label={isCollapsed ? t("signIn") : undefined}
            >
              <LogIn className="h-5 w-5 shrink-0 text-claude-orange" aria-hidden="true" />
              {!isCollapsed && <span className="text-claude-text">{t("signIn")}</span>}
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
