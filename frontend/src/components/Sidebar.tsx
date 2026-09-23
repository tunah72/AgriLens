"use client";

import React, { useState } from "react";
import { BookOpen, ChevronLeft, ChevronRight, History, Leaf, LogIn, Plus } from "lucide-react";
import type { UserResponse } from "../lib/api";
import { TabId } from "./TabNav";
import AccountMenu from "./ui/AccountMenu";

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
}

const menuItems = [
  {
    id: "knowledge" as TabId,
    label: "Knowledge Base",
    mobileLabel: "Knowledge",
    icon: BookOpen,
  },
  {
    id: "history" as TabId,
    label: "Diagnosis History",
    mobileLabel: "History",
    icon: History,
  },
];

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
}: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = controlledCollapsed ?? internalCollapsed;
  const toggleCollapsed = () => {
    const nextCollapsed = !isCollapsed;
    onCollapsedChange?.(nextCollapsed);
    if (controlledCollapsed === undefined) setInternalCollapsed(nextCollapsed);
  };

  return (
    <>
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
          <span>Diagnose</span>
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
          <div className="flex h-11 w-11 items-center justify-center text-claude-muted" role="status" aria-label="Loading account status">
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-claude-orange/30 border-t-claude-orange" aria-hidden="true" />
          </div>
        ) : user ? (
          <AccountMenu username={user.username} onLogout={logout} variant="mobile" />
        ) : (
          <button
            type="button"
            onClick={onLoginClick}
            className="inline-flex h-11 w-11 flex-col items-center justify-center rounded-xl border border-surface-border bg-surface-raised text-text-secondary shadow-sm transition-colors hover:bg-surface-sidebar hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar"
            aria-label="Sign in"
          >
            <LogIn className="h-5 w-5" aria-hidden="true" />
          </button>
        )}
      </nav>

      <aside
        className={`fixed left-0 top-0 z-30 hidden h-screen flex-col border-r border-surface-border bg-surface-sidebar transition-[width] duration-300 lg:flex ${
          isCollapsed ? "w-[72px]" : "w-64"
        }`}
        aria-label="Sidebar navigation"
      >
        <div className="flex h-16 items-center justify-between p-4">
          {!isCollapsed ? (
            <div className="flex items-center gap-2">
              <Leaf className="h-5 w-5 fill-claude-orange/10 text-claude-orange" aria-hidden="true" />
              <span className="text-lg font-serif font-bold tracking-tight text-foreground">PlantDisease AI</span>
            </div>
          ) : (
            <Leaf className="mx-auto h-5 w-5 text-claude-orange" aria-hidden="true" />
          )}
          <button
            type="button"
            onClick={toggleCollapsed}
            className="inline-flex h-11 w-11 items-center justify-center rounded-lg text-text-secondary transition-colors hover:bg-interactive-active hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar"
            aria-label={isCollapsed ? "Expand navigation bar" : "Collapse navigation bar"}
          >
            {isCollapsed ? <ChevronRight className="h-4 w-4" aria-hidden="true" /> : <ChevronLeft className="h-4 w-4" aria-hidden="true" />}
          </button>
        </div>

        <div className="mb-4 px-3">
          <button
            type="button"
            onClick={onNewDiagnosis}
            disabled={isPredictionSubmitting}
            className={`flex w-full min-h-11 items-center justify-center gap-2 rounded-lg border border-surface-border bg-surface-raised px-3 py-2 text-sm font-medium shadow-sm transition-colors hover:bg-surface-hover hover:border-border-hover disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar ${
              isCollapsed ? "rounded-full p-2" : ""
            } ${activeTab === "diagnosis" ? "border-claude-orange/60 ring-2 ring-claude-orange/20" : ""}`}
            title="New diagnosis"
          >
            <Plus className="h-4 w-4 shrink-0 text-claude-orange" aria-hidden="true" />
            {!isCollapsed && <span className="text-foreground">New diagnosis</span>}
          </button>
        </div>

        <nav className="flex-1 space-y-1 px-3" aria-label="Navigation items">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                type="button"
                aria-pressed={isActive}
                onClick={() => onTabChange(item.id)}
                className={`flex min-h-11 w-full items-center gap-3 rounded-lg p-2 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar ${
                  isActive
                    ? "bg-interactive-active font-medium text-claude-text"
                    : "text-text-secondary hover:bg-interactive-hover hover:text-claude-text"
                }`}
                aria-label={isCollapsed ? item.label : undefined}
              >
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-claude-orange" : "text-text-secondary"}`} aria-hidden="true" />
                {!isCollapsed && <span className="text-sm font-medium leading-none">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        <div className="border-t border-surface-border/50 p-3">
          {isLoading ? (
            <div className="flex min-h-11 items-center justify-center text-claude-muted" role="status" aria-label="Loading account status">
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-claude-orange/30 border-t-claude-orange" aria-hidden="true" />
            </div>
          ) : user ? (
            <AccountMenu username={user.username} onLogout={logout} variant={isCollapsed ? "mobile" : "sidebar"} />
          ) : (
            <button
              type="button"
              onClick={onLoginClick}
              className={`flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-surface-border bg-surface-raised px-3 py-2 text-xs font-semibold shadow-sm transition-colors hover:bg-surface-hover hover:border-border-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar ${
                isCollapsed ? "rounded-full p-2" : ""
              }`}
              title="Sign in"
              aria-label={isCollapsed ? "Sign in" : undefined}
            >
              <LogIn className="h-4 w-4 shrink-0 text-claude-orange" aria-hidden="true" />
              {!isCollapsed && <span className="text-claude-text">Sign in</span>}
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
