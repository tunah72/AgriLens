import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React, { useRef, useState } from "react";
import { describe, expect, it, vi } from "vitest";
import AuthModal from "../AuthModal";
import type { UseAuthReturn } from "../../hooks/useAuth";
import { LanguageProvider } from "../../lib/i18n";

vi.mock("../AuthForm", () => ({
  default: () => <form aria-label="Authentication form"><button type="submit">Sign In</button></form>,
}));

const auth = {
  user: null,
  token: null,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
} as unknown as UseAuthReturn;

describe("AuthModal", () => {
  it("provides a semantic dialog with AgriLens title and closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<AuthModal isOpen onClose={onClose} auth={auth} />);

    expect(screen.getByRole("dialog", { name: "Tài khoản AgriLens" })).toBeInTheDocument();

    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("supports English title when LanguageProvider is set to English", () => {
    render(
      <LanguageProvider defaultLang="en">
        <AuthModal isOpen onClose={vi.fn()} auth={auth} />
      </LanguageProvider>
    );

    expect(screen.getByRole("dialog", { name: "AgriLens Account" })).toBeInTheDocument();
  });

  it("uses a visible close button rather than overlay-only dismissal", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<AuthModal isOpen onClose={onClose} auth={auth} />);

    await user.click(screen.getByRole("button", { name: "Close dialog" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
  it("restores focus to the opener when the controlled dialog closes", async () => {
    const user = userEvent.setup();

    function ControlledAuthModal() {
      const [isOpen, setIsOpen] = useState(false);
      const triggerRef = useRef<HTMLButtonElement | null>(null);
      return (
        <>
          <button ref={triggerRef} type="button" onClick={() => setIsOpen(true)}>Open auth</button>
          <AuthModal isOpen={isOpen} onClose={() => setIsOpen(false)} auth={auth} restoreFocusRef={triggerRef} />
        </>
      );
    }

    render(<ControlledAuthModal />);
    const trigger = screen.getByRole("button", { name: "Open auth" });
    await user.click(trigger);
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(trigger).toHaveFocus();
  });

  it("does not override Radix focus restoration when the original opener is removed", async () => {
    const user = userEvent.setup();

    function ConditionalTriggerAuthModal() {
      const [isOpen, setIsOpen] = useState(false);
      const [showTrigger, setShowTrigger] = useState(true);
      const triggerRef = useRef<HTMLButtonElement | null>(null);
      const fallbackRef = useRef<HTMLButtonElement | null>(null);
      return (
        <>
          {showTrigger && <button ref={triggerRef} type="button" onClick={() => setIsOpen(true)}>Open auth</button>}
          <button ref={fallbackRef} type="button">Fallback focus target</button>
          <AuthModal
            isOpen={isOpen}
            onClose={() => {
              setShowTrigger(false);
              setIsOpen(false);
            }}
            auth={auth}
            restoreFocusRef={triggerRef}
            fallbackFocusRef={fallbackRef}
          />
        </>
      );
    }

    render(<ConditionalTriggerAuthModal />);
    await user.click(screen.getByRole("button", { name: "Open auth" }));
    await user.keyboard("{Escape}");

    expect(screen.queryByRole("button", { name: "Open auth" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Fallback focus target" })).toHaveFocus();
  });
});
