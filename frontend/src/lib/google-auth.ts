import { ApiError, apiPost } from './api';
import type { SessionResponse } from './types';

export interface GoogleStartResponse { state: string; verifier: string; expires_at: string }
export interface GoogleFlowProof { state: string; verifier: string }
export interface GoogleExchangeRequest extends GoogleFlowProof { session_id: string }
export interface GoogleLinkRequest extends GoogleFlowProof { password: string }
export interface GoogleExchangeResponse { status: 'authenticated' | 'link_required'; session: SessionResponse | null; email: string | null; password_available?: boolean | null }
export interface GoogleRecoveryResponse { reference: string; status: 'pending' | 'approved'; expires_at: string }
export interface ManagedGoogleIdentity { id: string; email: string; name: string; email_verified: boolean | null }

const PENDING_KEY = 'repforge.google-signin';

export function googleStartInNewTab(): boolean { return window.self !== window.top; }

export async function startGoogleSignIn(signal?: AbortSignal): Promise<void> {
  if (googleStartInNewTab()) {
    // Avoid embedding Google's account picker; the new app tab starts its own bound flow.
    window.open(`${window.location.origin}/?signin=google`, '_blank', 'noopener,noreferrer');
    return;
  }
  const flow = await apiPost<GoogleStartResponse>('/auth/google/start', undefined, { timeoutMs: 20000, signal });
  if (signal?.aborted) throw new DOMException('Sign-in cancelled', 'AbortError');
  try { sessionStorage.setItem(PENDING_KEY, JSON.stringify(flow)); }
  catch { throw new Error('Allow tab storage to use Google sign-in, or use your RepForge password.'); }
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const redirectUrl = new URL('/dashboard', window.location.origin);
  redirectUrl.searchParams.set('google_state', flow.state);
  window.location.assign(`https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl.toString())}`);
}

export function readGoogleProof(state: string | null): GoogleFlowProof | null {
  try {
    const flow = JSON.parse(sessionStorage.getItem(PENDING_KEY) || 'null') as GoogleStartResponse | null;
    if (!flow || !state || flow.state !== state || Date.parse(flow.expires_at) <= Date.now()) return null;
    return { state: flow.state, verifier: flow.verifier };
  } catch { return null; }
}

export function clearGoogleProof() { sessionStorage.removeItem(PENDING_KEY); }

export function googleError(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = (error.body as { detail?: unknown } | null)?.detail;
    if (typeof detail === 'string') return detail;
  }
  if (error instanceof Error && error.message.startsWith('Allow tab storage')) return error.message;
  return 'Google sign-in could not finish. Please restart it or use password sign-in.';
}