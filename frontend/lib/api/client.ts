import { getApiBaseUrl } from "@/lib/config";
import type { HttpMethod } from "@/lib/api/types";

export type QueryValue = string | number | boolean | null | undefined;

export interface ApiFetchOptions {
  method?: HttpMethod;
  body?: unknown;
  token?: string | null;
  query?: Record<string, QueryValue>;
  headers?: HeadersInit;
  baseUrl?: string;
  fetcher?: typeof fetch;
}

export class ApiClientError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(message: string, status: number, detail: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail;
  }
}

export function buildApiUrl(
  path: string,
  query?: Record<string, QueryValue>,
  baseUrl = getApiBaseUrl(),
): string {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(`${baseUrl}${cleanPath}`);

  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== null && value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

export async function apiFetch<TResponse>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<TResponse> {
  const {
    method = "GET",
    body,
    token,
    query,
    headers,
    baseUrl,
    fetcher = fetch,
  } = options;
  const requestHeaders = new Headers(headers);

  if (body !== undefined && !requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }
  if (token) {
    requestHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetcher(buildApiUrl(path, query, baseUrl), {
    method,
    headers: requestHeaders,
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await readErrorDetail(response);
    throw new ApiClientError(errorMessage(response, detail), response.status, detail);
  }

  return (await response.json()) as TResponse;
}

async function readErrorDetail(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function errorMessage(response: Response, detail: unknown): string {
  if (typeof detail === "string" && detail.trim().length > 0) {
    return detail;
  }
  if (isRecord(detail)) {
    const directDetail = detail.detail;
    if (typeof directDetail === "string" && directDetail.trim().length > 0) {
      return directDetail;
    }
    if (isRecord(directDetail) && typeof directDetail.message === "string") {
      return directDetail.message;
    }
    if (isRecord(detail.error) && typeof detail.error.message === "string") {
      return detail.error.message;
    }
  }
  return response.statusText || `Request failed with status ${response.status}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
