function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_BASE_URL && process.env.NEXT_PUBLIC_API_BASE_URL !== "http://localhost:8000/api/v1") {
    return process.env.NEXT_PUBLIC_API_BASE_URL;
  }
  if (typeof window !== "undefined") {
    const isLocal = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
    if (!isLocal) {
      return "/api/v1";
    }
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";
}

export const API_BASE_URL = getApiBaseUrl();
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
export const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
export const ALLOWED_IMAGE_EXTENSIONS = ".jpg,.jpeg,.png,.webp";
