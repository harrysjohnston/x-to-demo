/**
 * Auth helpers: login/register/logout and token storage.
 * Storage keys are in storage-keys.ts so the API client can use them without a circular dependency.
 */

import { ApiError, api } from "./api";
import { AUTH_ACCESS_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY } from "./storage-keys";

export { AUTH_ACCESS_TOKEN_KEY, AUTH_REFRESH_TOKEN_KEY };

export interface TokenResponse {
  token_type: string;
  access_token: string;
  refresh_token: string;
}

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(AUTH_ACCESS_TOKEN_KEY);
}

export function storeTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(AUTH_ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(AUTH_REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(AUTH_ACCESS_TOKEN_KEY);
  localStorage.removeItem(AUTH_REFRESH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getStoredAccessToken();
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const data = await api.post<TokenResponse>("/auth/login", { email, password });
  storeTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(
  name: string,
  email: string,
  password: string,
): Promise<TokenResponse> {
  await api.post("/auth/register", { name, email, password });
  return login(email, password);
}

export async function logout(): Promise<void> {
  const refreshToken =
    typeof window !== "undefined" ? localStorage.getItem(AUTH_REFRESH_TOKEN_KEY) : null;
  try {
    if (refreshToken) {
      await api.post("/auth/logout", { refresh_token: refreshToken });
    }
  } catch (e) {
    if (!(e instanceof ApiError) || e.status !== 401) throw e;
  } finally {
    clearTokens();
  }
}
