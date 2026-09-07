// Session boundary: auth is an httpOnly cookie the backend owns; the frontend's one
// duty is wiping the react-query cache so one account's data never renders for the next.
import { queryClient } from "./queryClient";
import { apiPost } from "./api";
import { clearToken, clearUserId } from './profile';

// Call after every successful login/signup.
export function beginSession(): void {
  queryClient.clear();
  window.dispatchEvent(new Event('repforge-session-changed'));
  localStorage.setItem('repforge.session-change', String(Date.now()));
}

// Called only AFTER successful server erasure, never instead of server deletion.
export function clearDeletedSession(): void {
  clearToken();
  clearUserId();
  for (const storage of [localStorage, sessionStorage]) {
    for (const key of Object.keys(storage)) {
      if (key.startsWith('repforge.') || key.startsWith('vocalpitch.')) storage.removeItem(key);
    }
  }
  localStorage.setItem('repforge.session-change', String(Date.now()));
  queryClient.clear();
  window.location.assign('/?data=deleted');
}

// Call from every sign-out control; the hard redirect resets all in-memory state.
export async function endSession(redirectTo: string = "/"): Promise<void> {
  try {
    await apiPost("/auth/logout");
  } finally {
    clearToken();
    clearUserId();
    localStorage.setItem('repforge.session-change', String(Date.now()));
    queryClient.clear();
    window.location.assign(redirectTo);
  }
}
