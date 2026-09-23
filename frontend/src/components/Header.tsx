"use client";

import React from "react";
import { Sun, Moon, Leaf, Globe } from "lucide-react";
import { useLanguage } from "../lib/i18n";

interface HeaderProps {
  activeTabLabel: string;
  theme: "light" | "dark";
  onThemeToggle: () => void;
}

export default function Header({ activeTabLabel, theme, onThemeToggle }: HeaderProps) {
  const { lang, setLang, t } = useLanguage();

  return (
    <header className="flex items-center justify-between px-4 sm:px-6 h-16 border-b border-surface-border bg-surface select-none sticky top-0 z-20 transition-colors duration-150">
      {/* Title / Context Tab Label */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 lg:hidden">
          <Leaf className="w-5 h-5 text-claude-orange" />
          <span className="font-serif font-bold text-claude-text text-base tracking-tight">{t("brand")}</span>
        </div>
        <span className="hidden lg:inline text-text-tertiary text-sm">/</span>
        <span className="text-xs font-semibold text-claude-text bg-surface-sidebar border border-surface-border px-2.5 py-1 rounded-md">
          {activeTabLabel}
        </span>
      </div>

      {/* Action Area: Language Switcher & Theme Toggle */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Language Switcher */}
        <button
          type="button"
          onClick={() => setLang(lang === "vi" ? "en" : "vi")}
          className="inline-flex h-11 items-center gap-1.5 px-3 rounded-xl border border-surface-border bg-surface-raised text-text-secondary text-xs font-semibold shadow-sm transition-all hover:bg-surface-sidebar hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2"
          title={lang === "vi" ? t("switchLanguage") : t("switchLanguage")}
          aria-label={t("switchLanguage")}
        >
          <Globe className="w-3.5 h-3.5 text-claude-orange" />
          <span className="font-medium">{lang === "vi" ? "VI" : "EN"}</span>
        </button>

        {/* Theme Toggle */}
        <button
          type="button"
          onClick={onThemeToggle}
          className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-surface-border bg-surface-raised text-text-secondary shadow-sm transition-all hover:bg-surface-sidebar hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2"
          title={theme === "light" ? t("switchThemeDark") : t("switchThemeLight")}
          aria-label={theme === "light" ? t("switchThemeDark") : t("switchThemeLight")}
        >
          {theme === "light" ? (
            <Moon className="w-4 h-4 text-stone-600" />
          ) : (
            <Sun className="w-4 h-4 text-amber-500" />
          )}
        </button>
      </div>
    </header>
  );
}
