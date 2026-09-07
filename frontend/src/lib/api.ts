// Typed fetch layer over the FastAPI backend. Base is the relative "/api" prefix so the
// same code works in dev (Vite proxies /api → :8001) and behind a single origin in prod.
const BASE = "/api";
import { getToken, clearToken, clearUserId } from './profile';

// Fields are declared, not constructor parameter properties: tsconfig sets
// erasableSyntaxOnly, which rejects `constructor(readonly status: number)`.
export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`request failed with ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

type JsonBody = unknown;

export function authHeaders(): Record<string, string> {
  try {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch (err) {
    console.error("could not read the session token", err);
    return {};
  }
}

export interface RequestOptions { signal?: AbortSignal; timeoutMs?: number; binary?: boolean }
async function request<T>(method: string, path: string, body?: JsonBody, options: RequestOptions = {}): Promise<T> {
  // Prefer the httpOnly cookie, with a short-lived bearer fallback for blocked cookies.
  const signal = options.signal ? AbortSignal.any([options.signal, AbortSignal.timeout(options.timeoutMs ?? 120000)]) : AbortSignal.timeout(options.timeoutMs ?? 120000);
  const res = await fetch(`${BASE}${path}`, {
    signal,
    method,
    credentials: "include",
    headers:
      body === undefined
        ? authHeaders()
        : { "Content-Type": "application/json", ...authHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  // FastAPI reports request-validation failures as 422 with a {detail: [...]} body.
  if (!res.ok) {
    const errBody = await res.json().catch(() => null);
    // Session gone: forget the cached id so the app falls back to the sign-in screen.
    if (res.status === 401) {
      try {
        clearUserId();
        clearToken();
        if (!path.startsWith('/auth/')) window.dispatchEvent(new Event('repforge-session-expired'));
      } catch (err) {
        console.error("could not clear the expired session", err);
      }
    }
    throw new ApiError(res.status, errBody);
  }

  if (res.status === 204) return undefined as T;
  if (options.binary) return await res.blob() as T;
  return (await res.json()) as T;
}

// The response type is yours to declare: nothing infers across the Python boundary, so a
// TS interface here mirrors the endpoint's Pydantic model by hand — keep the two in sync.
export const apiGet = <T>(path: string, options?: RequestOptions) => request<T>("GET", path, undefined, options);
export const apiPost = <T>(path: string, body?: JsonBody, options?: RequestOptions) => request<T>("POST", path, body ?? null, options);
export const apiAudio = (path: string, body: JsonBody, signal?: AbortSignal) => request<Blob>('POST', path, body, { signal, binary: true, timeoutMs: 55000 });
export const apiPut = <T>(path: string, body?: JsonBody) => request<T>("PUT", path, body ?? null);
export const apiPatch = <T>(path: string, body?: JsonBody) =>
  request<T>("PATCH", path, body ?? null);
export const apiDelete = <T>(path: string) => request<T>("DELETE", path);
