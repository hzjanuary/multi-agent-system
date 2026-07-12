import { apiFetch, type ApiFetchOptions } from "@/lib/api/client";
import type {
  CurrentUserResponse,
  LoginRequest,
  LogoutResponse,
  RefreshRequest,
  TokenResponse,
} from "@/lib/api/types";

type AuthRequestOptions = Pick<ApiFetchOptions, "baseUrl" | "fetcher">;

export function login(
  payload: LoginRequest,
  options: AuthRequestOptions = {},
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", {
    ...options,
    method: "POST",
    body: payload,
  });
}

export function refreshToken(
  payload: RefreshRequest,
  options: AuthRequestOptions = {},
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/refresh", {
    ...options,
    method: "POST",
    body: payload,
  });
}

export function logout(
  options: AuthRequestOptions = {},
): Promise<LogoutResponse> {
  return apiFetch<LogoutResponse>("/auth/logout", {
    ...options,
    method: "POST",
  });
}

export function getCurrentUser(
  accessToken: string,
  options: AuthRequestOptions = {},
): Promise<CurrentUserResponse> {
  return apiFetch<CurrentUserResponse>("/auth/me", {
    ...options,
    token: accessToken,
  });
}
