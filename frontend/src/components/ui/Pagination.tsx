"use client";

import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

interface PaginationProps {
  page: number;
  totalPages: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
}

type PageItem = number | "ellipsis";

function getPageItems(page: number, totalPages: number): PageItem[] {
  if (totalPages <= 5) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  if (page <= 3) return [1, 2, 3, "ellipsis", totalPages];
  if (page >= totalPages - 2) return [1, "ellipsis", totalPages - 2, totalPages - 1, totalPages];
  return [1, "ellipsis", page, "ellipsis", totalPages];
}

const controlClassName =
  "inline-flex h-11 min-w-11 items-center justify-center rounded-lg border border-surface-border bg-surface-raised px-2 text-sm font-semibold text-claude-text shadow-sm transition-colors hover:bg-surface-sidebar disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-background";

export default function Pagination({ page, totalPages, isLoading = false, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pageItems = getPageItems(page, totalPages);
  const goToPage = (nextPage: number) => {
    if (!isLoading && nextPage >= 1 && nextPage <= totalPages && nextPage !== page) {
      onPageChange(nextPage);
    }
  };

  return (
    <nav className="flex flex-col gap-3 border-t border-surface-border pt-4 sm:flex-row sm:items-center sm:justify-between" aria-label="Pagination">
      <p className="text-center text-xs font-medium text-claude-muted sm:text-left" aria-live="polite">
        Page {page} of {totalPages}
      </p>
      <div className="flex items-center justify-center gap-1.5">
        <button
          type="button"
          onClick={() => goToPage(page - 1)}
          disabled={isLoading || page === 1}
          className={controlClassName}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </button>
        {pageItems.map((item, index) =>
          item === "ellipsis" ? (
            <span key={`ellipsis-${index}`} className="inline-flex h-11 min-w-6 items-center justify-center text-claude-muted" aria-hidden="true">
              …
            </span>
          ) : (
            <button
              key={item}
              type="button"
              onClick={() => goToPage(item)}
              disabled={isLoading}
              aria-label={`Page ${item}`}
              aria-current={item === page ? "page" : undefined}
              className={cn(
                controlClassName,
                item === page && "border-claude-orange bg-interactive-active text-claude-text",
              )}
            >
              {item}
            </button>
          ),
        )}
        <button
          type="button"
          onClick={() => goToPage(page + 1)}
          disabled={isLoading || page === totalPages}
          className={controlClassName}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </nav>
  );
}
