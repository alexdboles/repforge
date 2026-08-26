# Security notes

No secrets in this document.

## Secret management
All credentials live in `backend/.env`, loaded with python-dotenv and read via
`os.environ` on the server: `JWT_SECRET`, `OPENAI_API_KEY`, `EMERGENT_LLM_KEY`,
`ELEVENLABS_API_KEY`, `MONGO_URL`. `backend/.env.example` documents the names
only. The frontend bundle contains no keys — every call goes to a relative
`/api/...` path through `src/lib/api.ts`.

## Authentication
Email + password accounts (`POST /api/auth/signup`, `/api/auth/login`) with
bcrypt password hashing, plus a throwaway guest session (`/api/auth/guest`) for
first-time visitors. The session is a signed JWT in an **httpOnly, Secure,
SameSite=Lax** cookie (`repforge_session`, 14 days). No token is stored in
localStorage; the browser keeps only a non-sensitive user id for UI state.
`/api/auth/logout` clears the cookie. Login and signup are rate limited per
client IP, and failures return a neutral message (no user enumeration).

## Authorization
Identity is always derived from the cookie (`lib/auth.current_user`) — a
`user_id` in a request body is ignored (see `start_simulation`). Every
user-owned route enforces ownership server-side:
- `require_self` on `/users/{id}/...`, attempts, assignments, sales profiles, journeys
- `require_owned` on simulations, sales profiles and custom scenarios; a foreign
  id returns **404**, so ids cannot be enumerated
- `require_org` on `/teams/{org}` and assignment writes (tenant boundary)
Profile updates use an explicit allow-list: `xp`, `level`, `badges`, `role` and
`org` are server-controlled and cannot be set from the browser. Scores and XP
are computed server-side from the stored transcript only.

## ElevenLabs
The API key never leaves the server. The browser POSTs text to
`/api/voice/speak`, which requires an authenticated session, caps text length,
resolves the voice from a server-side `persona → voice id` map (arbitrary voice
ids cannot be requested) and is rate limited per user. Upstream error bodies are
logged, never forwarded to the client.

## User data
Transcripts, scorecards, custom company profiles and progress are stored in
Mongo keyed by `user_id` and readable only by their owner. No raw audio is
stored: microphone audio is transcribed in the browser (Web Speech API) and only
text reaches the backend.

## Session / voice lifecycle
Ending a simulation is a privacy boundary. `End simulation` aborts speech
recognition (`abort()`, discarding pending results), bumps a TTS generation
token that invalidates in-flight `/api/voice/speak` requests and queued
playback, cancels speech synthesis and freezes the transcript. Late mutation
responses are discarded. Server-side, `complete` atomically claims the row
(`active → analyzing`), so double-clicks cannot double-analyse or double-award XP.

## Abuse protection
In-process fixed-window rate limits (`lib/auth.rate_limit`): TTS 300/h/user,
turns 240/h/user, simulation starts 40/h/user, hints 120/h/user, scenario
generation 30/h/user, login 10/5min/IP, signup 10/h/IP. Max 3 concurrent live
simulations per user; max 120 transcript turns per call; utterances capped at
2000 chars and TTS text at 1200.

## Prompt safety
Prompts contain scenario and transcript text only — never credentials. Model
output is parsed into Pydantic models and used solely for coaching content; it
never influences identity, roles, ownership or limits. AI text is rendered as
plain React text (no `dangerouslySetInnerHTML`), so injected markup cannot execute.

## Incident response
If exposure is suspected, rotate in this order and redeploy with new values in
the platform's secret store: `ELEVENLABS_API_KEY`, `OPENAI_API_KEY` /
`EMERGENT_LLM_KEY`, `JWT_SECRET` (invalidates all sessions), `MONGO_URL`.
