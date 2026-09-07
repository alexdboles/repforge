import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getToken, clearToken } from './profile';
const key = 'vocalpitch.session_token';
function storage() {
  const values = new Map<string, string>();
  return { getItem: (k: string) => values.get(k) ?? null, setItem: (k: string, v: string) => values.set(k, v), removeItem: (k: string) => values.delete(k) };
}
const token = (claims: object) => `header.${btoa(JSON.stringify(claims))}.signature`;
beforeEach(() => {
  vi.stubGlobal('window', globalThis);
  vi.stubGlobal('sessionStorage', storage());
  vi.stubGlobal('localStorage', storage());
});
afterEach(() => vi.unstubAllGlobals());
describe('session fallback', () => {
  it('migrates legacy tokens to tab storage', () => {
    const value = token({ exp: Date.now() / 1000 + 3600 });
    localStorage.setItem(key, value);
    expect(getToken()).toBe(value);
    expect(sessionStorage.getItem(key)).toBe(value);
    expect(localStorage.getItem(key)).toBeNull();
  });
  it.each([token({ exp: 1 }), token({}), 'malformed'])('clears invalid token %s', value => {
    sessionStorage.setItem(key, value);
    expect(getToken()).toBeNull();
    expect(sessionStorage.getItem(key)).toBeNull();
  });
  it('can clear a session when local storage is blocked', () => {
    sessionStorage.setItem(key, token({ exp: Date.now() / 1000 + 3600 }));
    vi.stubGlobal('localStorage', { removeItem() { throw new Error('blocked'); } });
    expect(getToken()).not.toBeNull();
    clearToken();
    expect(sessionStorage.getItem(key)).toBeNull();
  });
});
