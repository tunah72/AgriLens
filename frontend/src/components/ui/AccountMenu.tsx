"use client";

import React from "react";
import { DropdownMenu } from "radix-ui";
import { ChevronUp, LogOut, UserRound } from "lucide-react";
import { cn } from "../../lib/utils";

interface AccountMenuProps {
  username: string;
  onLogout: () => void;
  variant?: "sidebar" | "mobile";
}

function getInitials(username: string) {
  return username.slice(0, 2).toUpperCase() || "?";
}

export default function AccountMenu({ username, onLogout, variant = "sidebar" }: AccountMenuProps) {
  const isMobile = variant === "mobile";

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className={cn(
            "inline-flex items-center justify-center rounded-xl border border-surface-border bg-surface-raised text-text-secondary shadow-sm transition-colors hover:bg-surface-sidebar hover:text-claude-text focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-sidebar",
            isMobile ? "h-11 w-11 shrink-0" : "w-full min-h-11 gap-2.5 px-2.5 py-1.5 text-left",
          )}
          aria-label={`Open account menu for ${username}`}
        >
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-claude-orange/20 bg-claude-orange/10 text-xs font-bold font-serif text-claude-orange">
            {getInitials(username)}
          </span>
          {!isMobile && (
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold leading-tight text-claude-text">{username}</span>
              <span className="block text-[10px] font-medium leading-none text-claude-muted">Your Account</span>
            </span>
          )}
          {!isMobile && <ChevronUp className="h-4 w-4 shrink-0" aria-hidden="true" />}
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          side={isMobile ? "top" : "right"}
          align={isMobile ? "end" : "start"}
          sideOffset={8}
          collisionPadding={12}
          className="z-[60] w-[min(14rem,calc(100vw-1.5rem))] max-w-[calc(100vw-1.5rem)] rounded-xl border border-surface-border bg-surface-raised p-1.5 text-sm shadow-xl outline-none motion-safe:animate-fade-in"
        >
          <DropdownMenu.Label className="flex items-center gap-2 px-2.5 py-2 text-xs font-medium text-claude-muted">
            <UserRound className="h-4 w-4" aria-hidden="true" />
            <span className="min-w-0 flex-1 truncate">{username}</span>
          </DropdownMenu.Label>
          <DropdownMenu.Separator className="my-1 h-px bg-surface-border" />
          <DropdownMenu.Item
            onSelect={onLogout}
            className="flex min-h-11 cursor-pointer select-none items-center gap-2 rounded-lg px-2.5 py-2 text-danger-700 outline-none transition-colors data-[highlighted]:bg-danger-50 data-[highlighted]:text-danger-700 dark:data-[highlighted]:bg-danger-500/10"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign Out
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  );
}
