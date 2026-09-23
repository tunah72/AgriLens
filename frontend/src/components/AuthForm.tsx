"use client";

import React, { useEffect, useRef, useState } from "react";
import type { UseAuthReturn } from "../hooks/useAuth";
import { ApiError } from "../lib/api";

type AuthField = "username" | "email" | "password";

interface AuthFormProps {
  onSuccess: () => void;
  auth: UseAuthReturn;
  notice?: string | null;
}

const fieldIds: Record<AuthField, string> = {
  username: "auth-username",
  email: "auth-email",
  password: "auth-password",
};

const fieldHints: Record<AuthField, string> = {
  username: "Use 3 or more characters.",
  email: "Enter your active email address.",
  password: "Use 6 or more characters.",
};

export default function AuthForm({ onSuccess, auth, notice }: AuthFormProps) {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<AuthField, string>>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const inputRefs = useRef<Record<AuthField, HTMLInputElement | null>>({
    username: null,
    email: null,
    password: null,
  });

  useEffect(() => {
    if (notice) setFormError(notice);
  }, [notice]);

  const clearFieldError = (field: AuthField) => {
    setFieldErrors((current) => ({ ...current, [field]: undefined }));
    setFormError(null);
  };

  const switchMode = (nextLoginMode: boolean) => {
    setIsLoginMode(nextLoginMode);
    setFieldErrors({});
    setFormError(null);
  };

  const validate = () => {
    const nextErrors: Partial<Record<AuthField, string>> = {};

    if (username.trim().length < 3) {
      nextErrors.username = "Username must contain at least 3 characters.";
    }
    if (!isLoginMode && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      nextErrors.email = "Invalid email address.";
    }
    if (password.length < 6) {
      nextErrors.password = "Password must contain at least 6 characters.";
    }

    setFieldErrors(nextErrors);
    const firstInvalidField = (Object.keys(nextErrors) as AuthField[])[0];
    if (firstInvalidField) {
      inputRefs.current[firstInvalidField]?.focus();
      return false;
    }
    return true;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError(null);

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      if (isLoginMode) {
        await auth.login(username.trim(), password);
      } else {
        await auth.register(username.trim(), email.trim(), password);
      }
      onSuccess();
    } catch (error) {
      if (error instanceof ApiError) {
        setFieldErrors(error.fieldErrors);
        setFormError(error.message);
      } else {
        setFormError("Unable to complete authentication. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const getDescribedBy = (field: AuthField) => {
    const ids = [`${fieldIds[field]}-hint`];
    if (fieldErrors[field]) ids.push(`${fieldIds[field]}-error`);
    return ids.join(" ");
  };

  return (
    <div className="w-full space-y-5">
      <div className="flex border-b border-surface-border" aria-label="Select authentication method">
        <button
          type="button"
          onClick={() => switchMode(true)}
          aria-pressed={isLoginMode}
          className={`min-h-11 flex-1 border-b-2 pb-3 text-center text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised ${
            isLoginMode
              ? "border-claude-orange font-bold text-claude-orange"
              : "border-transparent text-text-secondary hover:text-claude-text"
          }`}
        >
          Sign In
        </button>
        <button
          type="button"
          onClick={() => switchMode(false)}
          aria-pressed={!isLoginMode}
          className={`min-h-11 flex-1 border-b-2 pb-3 text-center text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised ${
            !isLoginMode
              ? "border-claude-orange font-bold text-claude-orange"
              : "border-transparent text-text-secondary hover:text-claude-text"
          }`}
        >
          Sign Up
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="space-y-4"
        noValidate
        aria-busy={isSubmitting}
        aria-label={isLoginMode ? "Sign in form" : "Sign up form"}
      >
        <div>
          <label htmlFor={fieldIds.username} className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-claude-muted">
            Username
          </label>
          <input
            ref={(element) => { inputRefs.current.username = element; }}
            id={fieldIds.username}
            name="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => {
              setUsername(event.target.value);
              clearFieldError("username");
            }}
            disabled={isSubmitting}
            aria-invalid={Boolean(fieldErrors.username)}
            aria-describedby={getDescribedBy("username")}
            className="w-full rounded-xl border border-surface-border bg-input-bg px-3.5 py-2 text-sm transition-colors placeholder-stone-400 focus-visible:outline-none focus-visible:border-claude-orange focus-visible:ring-2 focus-visible:ring-claude-orange/20 disabled:bg-input-disabled disabled:text-text-tertiary"
            placeholder="farmer_john"
          />
          <p id={`${fieldIds.username}-hint`} className="mt-1 text-xs text-claude-muted">{fieldHints.username}</p>
          {fieldErrors.username && <p id={`${fieldIds.username}-error`} className="mt-1 text-xs font-medium text-danger-700">{fieldErrors.username}</p>}
        </div>

        {!isLoginMode && (
          <div>
            <label htmlFor={fieldIds.email} className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-claude-muted">
              Email Address
            </label>
            <input
              ref={(element) => { inputRefs.current.email = element; }}
              id={fieldIds.email}
              name="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
                clearFieldError("email");
              }}
              disabled={isSubmitting}
              aria-invalid={Boolean(fieldErrors.email)}
              aria-describedby={getDescribedBy("email")}
              className="w-full rounded-xl border border-surface-border bg-input-bg px-3.5 py-2 text-sm transition-colors placeholder-stone-400 focus-visible:outline-none focus-visible:border-claude-orange focus-visible:ring-2 focus-visible:ring-claude-orange/20 disabled:bg-input-disabled disabled:text-text-tertiary"
              placeholder="john@example.com"
            />
            <p id={`${fieldIds.email}-hint`} className="mt-1 text-xs text-claude-muted">{fieldHints.email}</p>
            {fieldErrors.email && <p id={`${fieldIds.email}-error`} className="mt-1 text-xs font-medium text-danger-700">{fieldErrors.email}</p>}
          </div>
        )}

        <div>
          <label htmlFor={fieldIds.password} className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-claude-muted">
            Password
          </label>
          <input
            ref={(element) => { inputRefs.current.password = element; }}
            id={fieldIds.password}
            name="password"
            type="password"
            autoComplete={isLoginMode ? "current-password" : "new-password"}
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              clearFieldError("password");
            }}
            disabled={isSubmitting}
            aria-invalid={Boolean(fieldErrors.password)}
            aria-describedby={getDescribedBy("password")}
            className="w-full rounded-xl border border-surface-border bg-input-bg px-3.5 py-2 text-sm transition-colors placeholder-stone-400 focus-visible:outline-none focus-visible:border-claude-orange focus-visible:ring-2 focus-visible:ring-claude-orange/20 disabled:bg-input-disabled disabled:text-text-tertiary"
            placeholder="••••••••"
          />
          <p id={`${fieldIds.password}-hint`} className="mt-1 text-xs text-claude-muted">{fieldHints.password}</p>
          {fieldErrors.password && <p id={`${fieldIds.password}-error`} className="mt-1 text-xs font-medium text-danger-700">{fieldErrors.password}</p>}
        </div>

        {formError && (
          <div role="alert" className="rounded-xl border border-danger-500/10 bg-danger-50 p-3 text-xs font-medium leading-relaxed text-danger-700 dark:bg-danger-500/10">
            {formError}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="flex min-h-11 w-full items-center justify-center rounded-xl bg-claude-orange px-4 py-2.5 text-sm font-semibold text-claude-orange-text shadow-sm transition-colors hover:bg-claude-orange-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-claude-orange focus-visible:ring-offset-2 focus-visible:ring-offset-surface-raised disabled:cursor-not-allowed disabled:bg-stone-200 disabled:text-stone-400"
        >
          {isSubmitting ? (
            <>
              <span className="mr-1.5 h-3.5 w-3.5 animate-spin rounded-full border-2 border-claude-orange-text/30 border-t-claude-orange-text" aria-hidden="true" />
              <span aria-live="polite">Processing credentials…</span>
            </>
          ) : isLoginMode ? (
            "Sign In"
          ) : (
            "Create Account & Sign In"
          )}
        </button>
      </form>
    </div>
  );
}
