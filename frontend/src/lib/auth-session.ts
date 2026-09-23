export const AUTH_SESSION_EXPIRED_EVENT = "plant-disease:session-expired";
export const SESSION_EXPIRED_MESSAGE = "Session has expired. Please sign in again.";

export type SessionExpiredDetail = {
  token: string;
};

export function notifySessionExpired(token: string) {
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<SessionExpiredDetail>(AUTH_SESSION_EXPIRED_EVENT, {
      detail: { token },
    }));
  }
}
