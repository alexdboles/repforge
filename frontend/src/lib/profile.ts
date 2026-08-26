// Lightweight local profile: the MVP identifies a rep by a stored user id.
const KEY = "vocalpitch.user_id";
// Session token fallback. The server's primary mechanism is an httpOnly cookie;
// browsers that block third-party cookies (e.g. the app inside a preview iframe)
// would otherwise loop back to the sign-in screen, so the same token is replayed
// as an Authorization header.
const TOKEN_KEY = "vocalpitch.session_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (err) {
    console.error("localStorage read failed", err);
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch (err) {
    console.error("localStorage write failed", err);
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (err) {
    console.error("localStorage write failed", err);
  }
}

export function getUserId(): string | null {
  try {
    return localStorage.getItem(KEY);
  } catch (err) {
    console.error("localStorage read failed", err);
    return null;
  }
}

export function setUserId(id: string): void {
  try {
    localStorage.setItem(KEY, id);
  } catch (err) {
    console.error("localStorage write failed", err);
  }
}

export function clearUserId(): void {
  try {
    localStorage.removeItem(KEY);
  } catch (err) {
    console.error("localStorage write failed", err);
  }
}

export function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function scoreTone(score: number): string {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

export function scoreBar(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-amber-500";
  return "bg-red-500";
}

export const MOMENT_TAGS: Record<string, { label: string; className: string }> = {
  "strong-question": { label: "Strong Question", className: "bg-emerald-100 text-emerald-800" },
  "missed-discovery": { label: "Missed Discovery", className: "bg-red-100 text-red-800" },
  objection: { label: "Objection", className: "bg-amber-100 text-amber-900" },
  "premature-pitch": { label: "Premature Pitch", className: "bg-orange-100 text-orange-900" },
  "strong-value": { label: "Strong Value", className: "bg-blue-100 text-blue-800" },
  "buying-signal": { label: "Buying Signal", className: "bg-violet-100 text-violet-800" },
  "closing-opportunity": { label: "Closing Opportunity", className: "bg-sky-100 text-sky-800" },
};

export function tagMeta(tag: string) {
  return MOMENT_TAGS[tag] ?? { label: tag, className: "bg-slate-100 text-slate-700" };
}
