"use client";

import React from "react";
import AuthForm from "./AuthForm";
import { useAuth } from "../hooks/useAuth";
import { Dialog, DialogContent } from "./ui/Dialog";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  auth: ReturnType<typeof useAuth>;
  sessionMessage?: string | null;
  restoreFocusRef?: React.RefObject<HTMLElement | null>;
  fallbackFocusRef?: React.RefObject<HTMLElement | null>;
}

export default function AuthModal({ isOpen, onClose, auth, sessionMessage, restoreFocusRef, fallbackFocusRef }: AuthModalProps) {
  return (
    <Dialog open={isOpen} onClose={onClose}>
      <DialogContent
        title="PlantDisease AI Account"
        description="Sign in to save and review your leaf diagnosis history."
        restoreFocusRef={restoreFocusRef}
        fallbackFocusRef={fallbackFocusRef}
      >
        <AuthForm onSuccess={onClose} auth={auth} notice={sessionMessage} />
      </DialogContent>
    </Dialog>
  );
}
