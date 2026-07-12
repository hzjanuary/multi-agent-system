import type { TokenResponse } from "@/lib/api/types";

export const ACCESS_TOKEN_STORAGE_KEY = "enterprise_os_access_token";
export const REFRESH_TOKEN_STORAGE_KEY = "enterprise_os_refresh_token";

export function getAccessToken(): string | null {
  return browserStorage()?.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? null;
}

export function setAccessToken(token: string): void {
  browserStorage()?.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
}

export function getRefreshToken(): string | null {
  return browserStorage()?.getItem(REFRESH_TOKEN_STORAGE_KEY) ?? null;
}

export function setRefreshToken(token: string): void {
  browserStorage()?.setItem(REFRESH_TOKEN_STORAGE_KEY, token);
}

export function setSessionTokens(tokens: TokenResponse): void {
  setAccessToken(tokens.access_token);
  setRefreshToken(tokens.refresh_token);
}

export function clearSessionTokens(): void {
  const storage = browserStorage();
  storage?.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  storage?.removeItem(REFRESH_TOKEN_STORAGE_KEY);
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

function browserStorage(): Storage | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage;
}
