/**
 * API client wrapper for consistent request/response handling.
 *
 * This provides a simple fetch wrapper that:
 * - Sets base URL and common headers
 * - Handles JSON serialization/deserialization
 * - Normalizes error responses to match API error format
 * - Provides typed request/response handling
 */

import { AUTH_ACCESS_TOKEN_KEY } from "./storage-keys";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ErrorDetail {
  code: string;
  message: string;
  field?: string | null;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface ResponseEnvelope<T> {
  data: T;
  meta?: Record<string, unknown> | null;
}

export interface ListResponseEnvelope<T> {
  data: T[];
  meta: {
    offset: number;
    limit: number;
    total?: number | null;
  };
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | null | undefined>;
}

/**
 * Builds a URL with query parameters.
 * Path is appended to the base (so "/uploads" with base "http://localhost:8000/api/v1"
 * becomes "http://localhost:8000/api/v1/uploads", not "http://localhost:8000/uploads").
 */
function buildUrl(
  path: string,
  params?: Record<string, string | number | boolean | null | undefined>,
): string {
  const base = API_BASE_URL.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const url = new URL(`${base}/${normalizedPath}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  return url.toString();
}

/**
 * Parses error response from API.
 */
async function parseErrorResponse(response: Response): Promise<ErrorResponse> {
  try {
    const data = await response.json();
    // Check if it matches our error format
    if (data.error && typeof data.error === "object") {
      return data as ErrorResponse;
    }
    // Fallback for non-standard error responses
    return {
      error: {
        code: `http_${response.status}`,
        message: data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`,
      },
    };
  } catch {
    // If JSON parsing fails, return a generic error
    return {
      error: {
        code: `http_${response.status}`,
        message: `HTTP ${response.status}: ${response.statusText}`,
      },
    };
  }
}

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public error: ErrorDetail,
    public response?: Response,
  ) {
    super(error.message);
    this.name = "ApiError";
  }
}

/**
 * Makes a request to the API.
 *
 * @param path - API endpoint path (will be prefixed with base URL)
 * @param options - Fetch options including optional params for query string
 * @returns Promise resolving to the response data (unwrapped from envelope)
 * @throws ApiError if the request fails
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options;

  // Build URL with query parameters
  const url = buildUrl(path, params);

  // Normalize headers to a plain object
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Convert fetchOptions.headers to a plain object if provided
  if (fetchOptions.headers) {
    if (fetchOptions.headers instanceof Headers) {
      fetchOptions.headers.forEach((value, key) => {
        headers[key] = value;
      });
    } else if (Array.isArray(fetchOptions.headers)) {
      fetchOptions.headers.forEach(([key, value]) => {
        headers[key] = value;
      });
    } else {
      Object.assign(headers, fetchOptions.headers);
    }
  }

  // Add Authorization header if token is available
  const token = typeof window !== "undefined" ? localStorage.getItem(AUTH_ACCESS_TOKEN_KEY) : null;
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    });

    // Handle 204 No Content (e.g., DELETE requests)
    if (response.status === 204) {
      return undefined as T;
    }

    // Handle error responses
    if (!response.ok) {
      const errorResponse = await parseErrorResponse(response);
      throw new ApiError(response.status, errorResponse.error, response);
    }

    // Parse successful response
    const data = await response.json();

    // Unwrap from envelope if present (for endpoints that return envelopes)
    // Some endpoints might return raw data, so we check for the envelope structure
    if (data && typeof data === "object" && "data" in data) {
      return data.data as T;
    }

    return data as T;
  } catch (error) {
    // Re-throw ApiError as-is
    if (error instanceof ApiError) {
      throw error;
    }
    // Wrap other errors (network errors, etc.)
    throw new ApiError(0, {
      code: "network_error",
      message: error instanceof Error ? error.message : "Network error occurred",
    });
  }
}

/**
 * Convenience methods for common HTTP verbs.
 */
export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: "GET" }),

  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    apiRequest<T>(path, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, options?: RequestOptions) =>
    apiRequest<T>(path, { ...options, method: "DELETE" }),
};
