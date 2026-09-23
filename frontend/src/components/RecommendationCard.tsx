"use client";

import React, { useState } from "react";
import { DiseaseRecommendation } from "../lib/api";
import { ChevronDown, ChevronUp, AlertCircle, BookOpen, ShieldCheck, HeartPulse, HelpCircle } from "lucide-react";

interface RecommendationCardProps {
  recommendation?: DiseaseRecommendation | null;
}

interface AccordionSectionProps {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  icon: React.ComponentType<any>;
  children: React.ReactNode;
}

function AccordionSection({ title, isOpen, onToggle, icon: Icon, children }: AccordionSectionProps) {
  return (
    <div className="border border-surface-border/50 rounded-xl overflow-hidden bg-background/50 dark:bg-black/10 transition-all duration-300 shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-surface-sidebar dark:hover:bg-zinc-800/50 transition-colors focus:outline-none"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-claude-orange" />
          <span className="text-sm font-display font-semibold text-foreground tracking-wide">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUp className="w-5 h-5 text-claude-muted" />
        ) : (
          <ChevronDown className="w-5 h-5 text-claude-muted" />
        )}
      </button>
      {isOpen && (
        <div className="p-5 border-t border-surface-border/50 bg-background/30 dark:bg-black/20 text-sm text-claude-text leading-relaxed animate-in fade-in duration-200">
          {children}
        </div>
      )}
    </div>
  );
}

export default function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    description: true,
    symptoms: true,
    treatments: true,
  });

  const toggleSection = (section: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  if (!recommendation) {
    return (
      <div className="w-full p-8 text-center py-12 space-y-4">
        <div className="mx-auto w-12 h-12 rounded-full bg-surface-sidebar flex items-center justify-center text-claude-muted">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div className="space-y-2">
          <p className="text-foreground font-display font-semibold text-lg">No expert recommendation available</p>
          <p className="text-sm text-claude-muted max-w-sm mx-auto">
            This classification label does not yet have supporting advice from plant protection specialists.
          </p>
        </div>
      </div>
    );
  }

  const {
    name_vi,
    name_en,
    description,
    symptoms = [],
    causes = [],
    treatments = [],
    prevention = [],
    advisory,
    sources = [],
  } = recommendation;

  return (
    <div className="w-full space-y-6">
      <div className="border-b border-surface-border/50 pb-4">
        <h4 className="text-xs font-display font-bold uppercase tracking-widest text-claude-orange/80">
          Expert Recommendation
        </h4>
        <h3 className="text-3xl md:text-4xl font-display font-bold text-foreground mt-2">
          {name_en || name_vi}
        </h3>
        {name_vi && name_en && (
          <p className="text-sm text-claude-muted italic mt-1">{name_vi}</p>
        )}
      </div>

      <div className="space-y-3">
        {description && (
          <AccordionSection
            title="Detailed Description"
            isOpen={!!openSections.description}
            onToggle={() => toggleSection("description")}
            icon={BookOpen}
          >
            <p className="leading-relaxed">{description}</p>
          </AccordionSection>
        )}

        {symptoms.length > 0 && (
          <AccordionSection
            title="Typical Symptoms"
            isOpen={!!openSections.symptoms}
            onToggle={() => toggleSection("symptoms")}
            icon={HelpCircle}
          >
            <ul className="list-disc pl-5 space-y-1.5">
              {symptoms.map((item, idx) => (
                <li key={idx} className="leading-relaxed">{item}</li>
              ))}
            </ul>
          </AccordionSection>
        )}

        {causes.length > 0 && (
          <AccordionSection
            title="Underlying Causes"
            isOpen={!!openSections.causes}
            onToggle={() => toggleSection("causes")}
            icon={AlertCircle}
          >
            <ul className="list-disc pl-5 space-y-1.5">
              {causes.map((item, idx) => (
                <li key={idx} className="leading-relaxed">{item}</li>
              ))}
            </ul>
          </AccordionSection>
        )}

        {treatments.length > 0 && (
          <AccordionSection
            title="Treatments & Remedies"
            isOpen={!!openSections.treatments}
            onToggle={() => toggleSection("treatments")}
            icon={HeartPulse}
          >
            <ul className="list-decimal pl-5 space-y-2 font-medium text-claude-text">
              {treatments.map((item, idx) => (
                <li key={idx} className="leading-relaxed">{item}</li>
              ))}
            </ul>
          </AccordionSection>
        )}

        {prevention.length > 0 && (
          <AccordionSection
            title="Prevention Measures"
            isOpen={!!openSections.prevention}
            onToggle={() => toggleSection("prevention")}
            icon={ShieldCheck}
          >
            <ul className="list-disc pl-5 space-y-1.5">
              {prevention.map((item, idx) => (
                <li key={idx} className="leading-relaxed">{item}</li>
              ))}
            </ul>
          </AccordionSection>
        )}
      </div>

      {advisory && (
        <div className="p-3.5 border-l-4 border-warning-500/50 bg-warning-50 dark:bg-warning-500/10 text-warning-700 dark:text-warning-400 dark:text-orange-200 rounded-r-xl text-xs leading-relaxed font-semibold">
          <span className="font-bold">Advisory Note: </span>
          {advisory}
        </div>
      )}

      {sources.length > 0 && (
        <div className="pt-4 border-t border-surface-border/50 space-y-2">
          <h5 className="text-[10px] font-bold text-claude-muted uppercase tracking-wider">
            References
          </h5>
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
            {sources.map((src, idx) => (
              <a
                key={idx}
                href={src.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-claude-orange hover:text-claude-orange-hover hover:underline transition-colors font-semibold"
              >
                {src.title}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
