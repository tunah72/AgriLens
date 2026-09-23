import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, getCurrentUser, loginUser, registerUser } from "../../lib/api";
import { AUTH_SESSION_EXPIRED_EVENT, SESSION_EXPIRED_MESSAGE } from "../../lib/auth-session";
import { AUTH_TOKEN_KEY, useAuth } from "../useAuth";

vi.mock("../../lib/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    code: string;
    fieldErrors: Record<string, string>;
    constructor({ status, code, message, fieldErrors = {} }: { status: number; code: string; message: string; fieldErrors?: Record<string, string> }) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
      this.fieldErrors = fieldErrors;
    }
  },
  getCurrentUser: vi.fn(),
  loginUser: vi.fn(),
  registerUser: vi.fn(),
}));

const mockGetCurrentUser = vi.mocked(getCurrentUser);
const mockLoginUser = vi.mocked(loginUser);
const mockRegisterUser = vi.mocked(registerUser);
const storage = new Map<string, string>();

const localStorageMock = {
  getItem: (key: string) => storage.get(key) ?? null,
  setItem: (key: string, value: string) => storage.set(key, value),
  removeItem: (key: string) => storage.delete(key),
  clear: () => storage.clear(),
};

describe("useAuth", () => {
  beforeEach(() => {
    Object.defineProperty(window, "localStorage", { value: localStorageMock, configurable: true });
    Object.defineProperty(globalThis, "localStorage", { value: localStorageMock, configurable: true });
    storage.clear();
    mockGetCurrentUser.mockReset();
    mockLoginUser.mockReset();
    mockRegisterUser.mockReset();
  });

  afterEach(() => vi.restoreAllMocks());

  it("clears stale local storage and authenticated state when restoring an expired token", async () => {
    localStorage.setItem(AUTH_TOKEN_KEY, "stale-token");
    mockGetCurrentUser.mockRejectedValue(new ApiError({
      status: 401,
      code: "SESSION_EXPIRED",
      message: "Session has expired. Please sign in again.",
    }));

    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.sessionMessage).toBe("Session has expired. Please sign in again.");
  });

  it("keeps automatic login after registration and clears local state on logout", async () => {
    mockRegisterUser.mockResolvedValue({ id: "1", username: "farmer", email: "farmer@example.com", is_active: true, created_at: "2026-07-15" });
    mockLoginUser.mockResolvedValue({ access_token: "new-token", token_type: "bearer" });
    mockGetCurrentUser.mockResolvedValue({ id: "1", username: "farmer", email: "farmer@example.com", is_active: true, created_at: "2026-07-15" });

    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(async () => {
      await result.current.register("farmer", "farmer@example.com", "secret1");
    });

    expect(result.current.user?.username).toBe("farmer");
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe("new-token");

    act(() => result.current.logout());
    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
  });

  it("clears an active authenticated shell when a protected request emits session expiry", async () => {
    mockLoginUser.mockResolvedValue({ access_token: "active-token", token_type: "bearer" });
    mockGetCurrentUser.mockResolvedValue({ id: "1", username: "farmer", email: "farmer@example.com", is_active: true, created_at: "2026-07-15" });

    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => {
      await result.current.login("farmer", "secret1");
    });
    expect(result.current.user?.username).toBe("farmer");

    act(() => window.dispatchEvent(new CustomEvent(AUTH_SESSION_EXPIRED_EVENT, { detail: { token: "active-token" } })));

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBeNull();
    expect(result.current.sessionMessage).toBe(SESSION_EXPIRED_MESSAGE);
  });

  it("ignores a late 401 from an earlier token after a new session is established", async () => {
    mockLoginUser.mockResolvedValue({ access_token: "new-token", token_type: "bearer" });
    mockGetCurrentUser.mockResolvedValue({ id: "2", username: "new-farmer", email: "new@example.com", is_active: true, created_at: "2026-07-15" });

    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => {
      await result.current.login("new-farmer", "secret1");
    });

    act(() => window.dispatchEvent(new CustomEvent(AUTH_SESSION_EXPIRED_EVENT, { detail: { token: "old-token" } })));

    expect(result.current.user?.username).toBe("new-farmer");
    expect(result.current.token).toBe("new-token");
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe("new-token");
    expect(result.current.sessionMessage).toBeNull();
  });

  it("keeps the newly issued registration session when /auth/me fails transiently", async () => {
    const registeredUser = { id: "3", username: "new-farmer", email: "new@example.com", is_active: true, created_at: "2026-07-15" };
    mockRegisterUser.mockResolvedValue(registeredUser);
    mockLoginUser.mockResolvedValue({ access_token: "issued-token", token_type: "bearer" });
    mockGetCurrentUser.mockRejectedValue(new ApiError({
      status: 0,
      code: "NETWORK_ERROR",
      message: "Unable to connect to the server. Please check your network and try again.",
    }));

    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await act(async () => {
      await result.current.register("new-farmer", "new@example.com", "secret1");
    });

    expect(result.current.user).toEqual(registeredUser);
    expect(result.current.token).toBe("issued-token");
    expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe("issued-token");
  });
});
