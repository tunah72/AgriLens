import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { API_BASE_URL } from "./constants";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function resolveImageUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("blob:") || url.startsWith("data:")) {
    return url;
  }

  let cleanUrl = url;
  const minioMatch = url.match(/https?:\/\/[^/]+\/plant-disease-images\/([^?#]+)/);
  if (minioMatch) {
    cleanUrl = `/api/v1/images/${minioMatch[1]}`;
  }

  if (cleanUrl.startsWith("/api/")) {
    if (typeof window !== "undefined" && API_BASE_URL.startsWith("http")) {
      try {
        const parsedBase = new URL(API_BASE_URL, window.location.origin);
        if (parsedBase.origin !== window.location.origin) {
          return `${parsedBase.origin}${cleanUrl}`;
        }
      } catch {
        // Fall back to relative URL
      }
    }
  }

  return cleanUrl;
}
