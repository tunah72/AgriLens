"use client";

import React from "react";
import { Stethoscope, BookOpen, History } from "lucide-react";

export type TabId = "diagnosis" | "knowledge" | "history";

interface TabNavProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export default function TabNav({ activeTab, onTabChange }: TabNavProps) {
  const tabs = [
    {
      id: "diagnosis" as TabId,
      label: "Diagnosis",
      icon: Stethoscope,
    },
    {
      id: "knowledge" as TabId,
      label: "Knowledge Base",
      icon: BookOpen,
    },
    {
      id: "history" as TabId,
      label: "History",
      icon: History,
    },
  ];

  return (
    <nav className="flex border-b border-stone-200" role="tablist">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 px-4 pb-3 text-sm font-semibold border-b-2 transition-all -mb-px outline-none focus:ring-0 ${
              isActive
                ? "border-healthy-700 text-healthy-700 font-bold"
                : "border-transparent text-stone-500 hover:text-stone-700 hover:border-stone-300"
            }`}
          >
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{tab.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
