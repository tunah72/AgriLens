import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  fetchHistory,
  getCurrentUser,
  loginUser,
  predictImage,
  registerUser,
} from "../api";
import { API_BASE_URL } from "../constants";
import { AUTH_SESSION_EXPIRED_EVENT } from "../auth-session";

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe("API client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("keeps the bearer contract for authenticated prediction requests", async () => {
    const file = new File(["leaf"], "leaf.png", { type: "image/png" });
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse({ prediction: "Healthy", confidence: 0.9, top_k: [] }));

    await predictImage(file, "demo-token");

    expect(fetchSpy).toHaveBeenCalledWith(`${API_BASE_URL}/predict`, expect.objectContaining({
      method: "POST",
      headers: { Authorization: "Bearer demo-token" },
      body: expect.any(FormData),
    }));
  });

  it("returns a typed, localized error for invalid login without exposing backend detail", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse({ detail: "Incorrect username or password" }, 401));

    await expect(loginUser({ username: "farmer", password: "wrong" })).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      code: "INVALID_CREDENTIALS",
      message: "Incorrect username or password.",
    });
  });

  it("maps duplicate registration to a safe field error", async () => {
    vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse({ detail: "Email already exists" }, 409));

    await expect(registerUser({ username: "farmer", email: "farmer@example.com", password: "secret1" })).rejects.toMatchObject({
      status: 409,
      code: "ACCOUNT_EXISTS",
      fieldErrors: { email: "This email address is already in use." },
    });
  });

  it("maps validation, file-size, server, and network failures to safe messages", async () => {
    const fetchSpy = vi.spyOn(global, "fetch");
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: [{ loc: ["body", "username"], msg: "too short" }] }, 422));
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: "large" }, 413));
    fetchSpy.mockResolvedValueOnce(jsonResponse({ detail: "database password leaked" }, 500));
    fetchSpy.mockRejectedValueOnce(new TypeError("Failed to fetch"));

    await expect(registerUser({ username: "ab", email: "bad", password: "123" })).rejects.toMatchObject({
      status: 422,
      fieldErrors: { username: "Invalid input for this field." },
    });
    await expect(predictImage(new File(["leaf"], "leaf.png", { type: "image/png" }))).rejects.toMatchObject({
      status: 413,
      message: "Uploaded file exceeds the maximum allowed size.",
    });
    await expect(loginUser({ username: "farmer", password: "secret1" })).rejects.toMatchObject({
      status: 500,
      message: "The server encountered an error. Please try again later.",
    });
    await expect(loginUser({ username: "farmer", password: "secret1" })).rejects.toMatchObject({
      status: 0,
      code: "NETWORK_ERROR",
      message: "Unable to connect to the server. Please check your network and try again.",
    });
  });

  it("notifies the auth boundary when a protected request receives 401", async () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, listener);
    vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse({ detail: "Could not validate credentials" }, 401));

    await expect(fetchHistory("stale-token")).rejects.toBeInstanceOf(ApiError);

    expect(listener).toHaveBeenCalledTimes(1);
    expect((listener.mock.calls[0][0] as CustomEvent<{ token: string }>).detail).toEqual({ token: "stale-token" });
    window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, listener);
  });

  it("keeps /me unauthorized handling opt-in for the auth hook", async () => {
    const listener = vi.fn();
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, listener);
    vi.spyOn(global, "fetch").mockResolvedValueOnce(jsonResponse({ detail: "Could not validate credentials" }, 401));

    await expect(getCurrentUser("stale-token", false)).rejects.toMatchObject({ status: 401 });

    expect(listener).not.toHaveBeenCalled();
    window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, listener);
  });
});
