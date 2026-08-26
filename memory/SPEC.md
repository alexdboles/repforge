# VocalPitch — AI Voice Sales Training Simulator

## What it does
A "sales flight simulator". A rep picks an exercise + difficulty, reads a pre-call brief,
holds a live voice conversation with an AI prospect (Claude Sonnet 4.5 via the Emergent
universal key), ends the call, and receives an AI scorecard with competency scores,
quoted strengths/misses, coaching priorities, communication analytics and a tagged
transcript. Progress, XP/levels/badges/streaks and history are persisted in MongoDB.

## Stack
FastAPI (`/api` router) + motor/Mongo; Vite + React 19 + TS strict + Tailwind v4 + shadcn.
Voice: browser Web Speech API (`SpeechRecognition` for mic, `speechSynthesis` for the
prospect's voice). A typed-reply input is always available as a fallback for browsers
without speech recognition (including headless Chromium in tests).

## Auth
No passwords. `POST /api/users` creates a profile; the id is stored in localStorage under
`vocalpitch.user_id`. Landing page creates the profile ("Demo Rep" if no name given).

## Data model (Mongo)
- `users`: id, name, role, experience_level, org, xp, level, streak, last_practice_date, badges, created_at
- `simulations`: id, user_id, exercise_id/name, difficulty/name, scenario (full incl. hidden),
  status (active|completed), transcript[{speaker,text,at}], started_at, ended_at,
  duration_seconds, evaluation, xp_awarded
- Static catalog in `backend/lib/catalog.py`: 8 exercises, 5 difficulties, 5 scenarios
  (each with `known` public intel and `hidden` intel the rep must discover), 14 skill
  categories, 8 badges.

## Key API routes (all under /api)
- GET `/exercises`, `/difficulties`, `/skills`, `/exercises/{id}/scenarios`
- POST `/users`, GET/PATCH `/users/{id}`, GET `/users/{id}/dashboard`, GET `/users/{id}/simulations`
- POST `/simulations` (starts a call; returns prospect's opening line)
- POST `/simulations/{id}/turns` {text, at} → prospect reply
- POST `/simulations/{id}/complete` → runs the coaching evaluation, awards XP
- GET `/simulations/{id}`

## Important behaviours
- Hidden scenario intel is stripped from API responses while a simulation is `active`
  and revealed only after completion (scorecard "What was hidden" tab).
- Ending a call with zero rep turns returns 422 with a clear message.
- Difficulty above the unlocked tier is selectable (with a warning toast) so judges can
  try Level 5 immediately.

## Frontend routes
`/` landing · `/dashboard` · `/training` (exercise + difficulty + brief) ·
`/simulation/:id` (dark cockpit) · `/scorecard/:id` · `/progress` · `/history` · `/profile`

## Seed data
None required — the catalog is code-level and always present. No user accounts are
pre-seeded; the landing CTA creates one.


---

# V2 — Learning platform + Practice My Business

## The two paths
1. **Guided training** (`/training` → `/learn/:exerciseId`) — 3 steps per skill:
   - **Learn**: why it matters, when it's used, key terms, a named framework, weak-vs-strong
     examples with "why it's stronger", beginner mistakes, what strong looks like, and an
     ungraded knowledge check. Content is per-skill, never generic.
   - **Scenario**: seller role + a full fictional product sheet (features, benefits, pricing,
     differentiators, limitations, use cases), the prospect, known info, objective and the
     skills being evaluated. Hidden prospect intel is never shown.
   - **Prepare**: one-page prep sheet, difficulty selector, "Start voice simulation".
   All steps are skippable ("Skip to the call"), and re-readable from the scorecard.
2. **Practice My Business** (`/practice-business`) — saved sales profiles → skill → difficulty →
   optional preferences → AI-generated custom scenario → brief → simulation → coaching.
   Setup wizard at `/practice-business/setup[/:profileId]` (7 short steps).

## Curriculum
`backend/lib/curriculum.py` — 8 modules (cold-call, discovery, value-statement, commercial-30s,
objection-handling, closing, in-person, phone-sales). Each carries `focus_categories`
(exercise-specific scorecard weighting) and `graded_principles` (the taught principles the
evaluator must grade). The evaluator is told to grade only those principles plus basic
conversational competence — no secret rules — and that different wording can score equally well.

## New API routes
- GET `/api/curriculum`, `/api/curriculum/{exercise_id}`
- POST/GET `/api/users/{id}/sales-profiles`, GET/PATCH/DELETE `/api/sales-profiles/{id}`
- POST `/api/custom-scenarios` {profile_id, exercise_id, difficulty, preferences} — LLM-generated
  prospect with controlled randomisation (personality, interest, urgency, authority, incumbent,
  style) so repeats never match. `hidden` is stored server-side only.
- GET `/api/voice/status`, POST `/api/voice/speak` {text, persona, difficulty}
- POST `/api/simulations` now takes `mode` ("guided"|"business") and `custom_scenario_id`.

## Voice
ElevenLabs proxied through `POST /api/voice/speak` — the key stays server-side and is read from
`ELEVENLABS_API_KEY` in backend/.env. `voice_persona` is derived server-side from the prospect's
personality/role and maps to a stock ElevenLabs voice; difficulty modulates the voice settings
(higher difficulty = terser, less warm). **If the key is absent the app reports
provider "browser" and falls back to browser speech synthesis** — no feature is faked.
Cockpit shows four explicit states: Your turn / Listening / Prospect thinking / Prospect speaking.

## Mongo collections added
`sales_profiles`, `custom_scenarios` (stores `hidden` + a snapshot of the profile).
