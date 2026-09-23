import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AuthForm from "../AuthForm";
import type { UseAuthReturn } from "../../hooks/useAuth";
import { ApiError } from "../../lib/api";

function makeAuth(overrides: Partial<UseAuthReturn> = {}) {
  return {
    user: null,
    token: null,
    isLoading: false,
    sessionMessage: null,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    clearSessionMessage: vi.fn(),
    ...overrides,
  } as unknown as UseAuthReturn;
}

describe("AuthForm", () => {
  it("associates visible login labels, help text, and autocomplete values", () => {
    render(<AuthForm auth={makeAuth()} onSuccess={vi.fn()} />);

    const username = screen.getByLabelText("Username");
    const password = screen.getByLabelText("Password");
    expect(username).toHaveAttribute("autocomplete", "username");
    expect(password).toHaveAttribute("autocomplete", "current-password");
    expect(username).toHaveAttribute("aria-describedby", "auth-username-hint");
    expect(password).toHaveAttribute("aria-describedby", "auth-password-hint");
  });

  it("associates registration fields and uses registration autocomplete values", async () => {
    const user = userEvent.setup();
    render(<AuthForm auth={makeAuth()} onSuccess={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Sign Up" }));

    expect(screen.getByLabelText("Username")).toHaveAttribute("autocomplete", "username");
    expect(screen.getByLabelText("Email Address")).toHaveAttribute("autocomplete", "email");
    expect(screen.getByLabelText("Password")).toHaveAttribute("autocomplete", "new-password");
  });

  it("shows associated validation errors and focuses the first invalid field", async () => {
    const user = userEvent.setup();
    render(<AuthForm auth={makeAuth()} onSuccess={vi.fn()} />);

    await user.click(within(screen.getByRole("form", { name: "Sign in form" })).getByRole("button", { name: "Sign In" }));

    const username = screen.getByLabelText("Username");
    expect(username).toHaveFocus();
    expect(username).toHaveAttribute("aria-invalid", "true");
    expect(username).toHaveAttribute("aria-describedby", "auth-username-hint auth-username-error");
    expect(screen.getByText("Username must contain at least 3 characters.")).toHaveAttribute("id", "auth-username-error");
  });

  it("prevents duplicate submits and announces the loading action", async () => {
    const user = userEvent.setup();
    let resolveLogin: (() => void) | undefined;
    const login = vi.fn(() => new Promise<void>((resolve) => { resolveLogin = resolve; }));
    render(<AuthForm auth={makeAuth({ login })} onSuccess={vi.fn()} />);

    await user.type(screen.getByLabelText("Username"), "farmer");
    await user.type(screen.getByLabelText("Password"), "secret1");
    const submit = within(screen.getByRole("form", { name: "Sign in form" })).getByRole("button", { name: "Sign In" });
    await user.click(submit);

    expect(submit).toBeDisabled();
    expect(screen.getByText("Processing credentials…")).toBeVisible();
    await user.click(submit);
    expect(login).toHaveBeenCalledTimes(1);

    resolveLogin?.();
    await waitFor(() => expect(submit).toBeEnabled());
  });

  it("closes only after successful login and localizes invalid credentials", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    const login = vi.fn().mockRejectedValue(new ApiError({
      status: 401,
      code: "INVALID_CREDENTIALS",
      message: "Incorrect username or password.",
    }));
    render(<AuthForm auth={makeAuth({ login })} onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText("Username"), "farmer");
    await user.type(screen.getByLabelText("Password"), "secret1");
    await user.click(within(screen.getByRole("form", { name: "Sign in form" })).getByRole("button", { name: "Sign In" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Incorrect username or password.");
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("closes the modal only after login resolves successfully", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    const login = vi.fn().mockResolvedValue(undefined);
    render(<AuthForm auth={makeAuth({ login })} onSuccess={onSuccess} />);

    await user.type(screen.getByLabelText("Username"), "farmer");
    await user.type(screen.getByLabelText("Password"), "secret1");
    await user.click(within(screen.getByRole("form", { name: "Sign in form" })).getByRole("button", { name: "Sign In" }));

    await waitFor(() => expect(login).toHaveBeenCalledWith("farmer", "secret1"));
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("keeps automatic login after registration and exposes duplicate email safely", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();
    const register = vi.fn().mockResolvedValue(undefined);
    render(<AuthForm auth={makeAuth({ register })} onSuccess={onSuccess} />);

    await user.click(screen.getByRole("button", { name: "Sign Up" }));
    await user.type(screen.getByLabelText("Username"), "farmer");
    await user.type(screen.getByLabelText("Email Address"), "farmer@example.com");
    await user.type(screen.getByLabelText("Password"), "secret1");
    await user.click(within(screen.getByRole("form", { name: "Sign up form" })).getByRole("button", { name: "Create Account & Sign In" }));

    await waitFor(() => expect(register).toHaveBeenCalledWith("farmer", "farmer@example.com", "secret1"));
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("does not render raw backend exception text", async () => {
    const user = userEvent.setup();
    const register = vi.fn().mockRejectedValue(new ApiError({
      status: 409,
      code: "ACCOUNT_EXISTS",
      message: "Username or email address is already in use.",
      fieldErrors: { email: "This email address is already in use." },
    }));
    render(<AuthForm auth={makeAuth({ register })} onSuccess={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Sign Up" }));
    await user.type(screen.getByLabelText("Username"), "farmer");
    await user.type(screen.getByLabelText("Email Address"), "farmer@example.com");
    await user.type(screen.getByLabelText("Password"), "secret1");
    await user.click(within(screen.getByRole("form", { name: "Sign up form" })).getByRole("button", { name: "Create Account & Sign In" }));

    expect(await screen.findByText("This email address is already in use.")).toBeVisible();
    expect(screen.queryByText(/database password leaked/i)).not.toBeInTheDocument();
  });
});
