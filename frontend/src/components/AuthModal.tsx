"use client";

import React from "react";
import AuthForm from "./AuthForm";
import type { UseAuthReturn } from "../hooks/useAuth";
import { Dialog, DialogContent } from "./ui/Dialog";
import { useLanguage } from "../lib/i18n";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  auth: UseAuthReturn;
  sessionMessage?: string | null;
  restoreFocusRef?: React.RefObject<HTMLElement | null>;
  fallbackFocusRef?: React.RefObject<HTMLElement | null>;
}

export default function AuthModal({
  isOpen,
  onClose,
  auth,
  sessionMessage,
  restoreFocusRef,
  fallbackFocusRef,
}: AuthModalProps) {
  const { t } = useLanguage();

  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent
        title={t("authTitle")}
        description={t("authDesc")}
        restoreFocusRef={restoreFocusRef}
        fallbackFocusRef={fallbackFocusRef}
      >
        <AuthForm onSuccess={onClose} auth={auth} notice={sessionMessage} />
      </DialogContent>
    </Dialog>
  );
}
