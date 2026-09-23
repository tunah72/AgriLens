import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AccountMenu from "../ui/AccountMenu";

describe("AccountMenu", () => {
  it("keeps logout in an account menu", async () => {
    const user = userEvent.setup();
    const onLogout = vi.fn();

    const veryLongUsername = "a".repeat(50);
    render(<AccountMenu username={veryLongUsername} onLogout={onLogout} variant="mobile" />);

    await user.click(screen.getByRole("button", { name: `Open account menu for ${veryLongUsername}` }));
    expect(screen.getByRole("menuitem", { name: "Sign Out" })).toBeVisible();
    expect(screen.getByText(veryLongUsername)).toHaveClass("min-w-0", "flex-1", "truncate");
    expect(screen.getByRole("menu")).toHaveClass("w-[min(14rem,calc(100vw-1.5rem))]", "max-w-[calc(100vw-1.5rem)]");

    await user.click(screen.getByRole("menuitem", { name: "Sign Out" }));
    expect(onLogout).toHaveBeenCalledTimes(1);
  });
});
