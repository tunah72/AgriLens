"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ApiError, getCurrentUser, loginUser, registerUser, UserResponse } from "../lib/api";
import {
  AUTH_SESSION_EXPIRED_EVENT,
  SESSION_EXPIRED_MESSAGE,
  type SessionExpiredDetail,
} from "../lib/auth-session";

export const AUTH_TOKEN_KEY = "plant_disease_token";

export function useAuth() {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sessionMessage, setSessionMessage] = useState<string | null>(null);
  const activeTokenRef = useRef<string | null>(null);

  const setActiveToken = useCallback((nextToken: string | null) => {
    activeTokenRef.current = nextToken;
    setToken(nextToken);
  }, []);

  const clearAuthState = useCallback((message?: string) => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setActiveToken(null);
    setUser(null);
    if (message) setSessionMessage(message);
  }, [setActiveToken]);

  useEffect(() => {
    const handleSessionExpired = (event: Event) => {
      const expiredToken = (event as CustomEvent<SessionExpiredDetail>).detail?.token;
      if (expiredToken && expiredToken === activeTokenRef.current) {
        clearAuthState(SESSION_EXPIRED_MESSAGE);
      }
    };
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, handleSessionExpired);
  }, [clearAuthState]);

  // Restore token and user on mount
  useEffect(() => {
    async function restoreSession() {
      const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
      if (storedToken) {
        activeTokenRef.current = storedToken;
        try {
          const userData = await getCurrentUser(storedToken, false);
          if (activeTokenRef.current === storedToken) {
            setActiveToken(storedToken);
            setUser(userData);
          }
        } catch (error) {
          if (activeTokenRef.current === storedToken) {
            clearAuthState(error instanceof ApiError && error.status === 401 ? SESSION_EXPIRED_MESSAGE : undefined);
          }
        }
      }
      setIsLoading(false);
    }
    void restoreSession();
  }, [clearAuthState, setActiveToken]);

  const login = useCallback(async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const loginRes = await loginUser({ username, password });
      localStorage.setItem(AUTH_TOKEN_KEY, loginRes.access_token);
      setActiveToken(loginRes.access_token);

      const userData = await getCurrentUser(loginRes.access_token, false);
      setUser(userData);
    } catch (err) {
      clearAuthState();
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearAuthState, setActiveToken]);

  const register = useCallback(async (username: string, email: string, password: string) => {
    setIsLoading(true);
    try {
      const registeredUser = await registerUser({ username, email, password });
      // Automatically login after successful registration
      const loginRes = await loginUser({ username, password });
      localStorage.setItem(AUTH_TOKEN_KEY, loginRes.access_token);
      setActiveToken(loginRes.access_token);

      try {
        const userData = await getCurrentUser(loginRes.access_token, false);
        setUser(userData);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clearAuthState(SESSION_EXPIRED_MESSAGE);
          throw error;
        }
        // Registration and token issuance already succeeded. The registration response is
        // safe to use for the authenticated shell while a transient profile request recovers.
        setUser(registeredUser);
      }
    } catch (err) {
      if (activeTokenRef.current === null) {
        clearAuthState();
      }
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [clearAuthState, setActiveToken]);

  const logout = useCallback(() => {
    clearAuthState();
    setSessionMessage(null);
  }, [clearAuthState]);

  const clearSessionMessage = useCallback(() => setSessionMessage(null), []);

  return {
    user,
    token,
    isLoading,
    sessionMessage,
    login,
    register,
    logout,
    clearSessionMessage,
  };
}
export type UseAuthReturn = ReturnType<typeof useAuth>;
