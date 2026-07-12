const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
const DEFAULT_WS_BASE_URL = "ws://localhost:8000/api/v1";

export function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, "");
}

export function getApiBaseUrl(): string {
  return normalizeBaseUrl(
    process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL,
  );
}

export function getWsBaseUrl(): string {
  return normalizeBaseUrl(
    process.env.NEXT_PUBLIC_WS_BASE_URL ?? DEFAULT_WS_BASE_URL,
  );
}
