import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AccountMenu from "../ui/AccountMenu";
import { LanguageProvider } from "../../lib/i18n";

describe("AccountMenu", () => {
  it("keeps logout in an account menu in Vietnamese by default", async () => {
    const user = userEvent.setup();
    const onLogout = vi.fn();

    const veryLongUsername = "a".repeat(50);
    render(<AccountMenu username={veryLongUsername} onLogout={onLogout} variant="mobile" />);

    await user.click(screen.getByRole("button", { name: `Open account menu for ${veryLongUsername}` }));
    expect(screen.getByRole("menuitem", { name: "Đăng xuất" })).toBeVisible();
    expect(screen.getByText(veryLongUsername)).toHaveClass("min-w-0", "flex-1", "truncate");
    expect(screen.getByRole("menu")).toHaveClass("w-[min(14rem,calc(100vw-1.5rem))]", "max-w-[calc(100vw-1.5rem)]");

    await user.click(screen.getByRole("menuitem", { name: "Đăng xuất" }));
    expect(onLogout).toHaveBeenCalledTimes(1);
  });

  it("supports English Sign Out when LanguageProvider is English", async () => {
    const user = userEvent.setup();
    const onLogout = vi.fn();

    render(
      <LanguageProvider defaultLang="en">
        <AccountMenu username="farmer_john" onLogout={onLogout} variant="mobile" />
      </LanguageProvider>
    );

    await user.click(screen.getByRole("button", { name: "Open account menu for farmer_john" }));
    expect(screen.getByRole("menuitem", { name: "Sign Out" })).toBeVisible();
  });
});
