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

---

# V3 — Skill gates, attempt comparison, team view, ElevenLabs

- **Skill gates**: `users.trained_skills[]`. `POST /api/users/{id}/trained/{exercise_id}` is called
  when the rep reaches the Prepare step of `/learn/:skill`; it unlocks that skill permanently.
  Until then the Training library's "Skip training, start the call" button is disabled and the
  exercise card shows no "Training complete" marker.
- **Attempt comparison**: `GET /api/users/{id}/attempts/{exercise_id}` returns every graded attempt
  with per-category scores, first→latest delta, most improved and still-weakest categories.
  Rendered by `components/AttemptComparison.tsx` on the scorecard ("Versus your previous attempts")
  and on Progress with an exercise picker. Needs 2+ attempts, otherwise shows a prompt.
- **Team view** (`/team`): `GET /api/teams/{org}` aggregates every user sharing `users.org` —
  member table (reps, avg, trend, weakest skill, last practice), shared skill gaps, leaderboard,
  exercise coverage chart and manager hours saved (30 min per role-play displaced). Read-only preview.
- **ElevenLabs**: `ELEVENLABS_API_KEY` is set in backend/.env. `/api/voice/status` reports
  provider=elevenlabs, but `POST /api/voice/speak` returns 502 wrapping ElevenLabs' 401
  `missing_permissions: text_to_speech` — the supplied key lacks the Text-to-Speech scope.
  The frontend degrades to browser speech synthesis automatically, so voice never breaks.
  Fix by enabling Text to Speech on the key (ElevenLabs → Profile → API Keys → edit scopes).

---

# V4 — ElevenLabs live, assigned training, streak nudges, same-prospect retry

- **ElevenLabs is ACTIVE.** `ELEVENLABS_API_KEY` in backend/.env now has the Text-to-Speech scope;
  `POST /api/voice/speak` returns audio/mpeg. Frontend labels it "ElevenLabs voice" in the cockpit
  and still auto-degrades to browser speech synthesis on any failure.
- **Assigned training** (`assignments` collection): `POST /api/assignments`
  {user_id, exercise_id, difficulty, note, assigned_by, org}; `GET /api/users/{id}/assignments`;
  `GET /api/teams/{org}/assignments`; `DELETE /api/assignments/{id}`. Completing a simulation for
  that exercise auto-closes the oldest matching pending assignment and records the score.
  Manager UI: Assign button per rep on `/team` + an "Assigned training" tracker. Rep UI:
  "Assigned to you" card on the dashboard with a Start link into the guided module.
- **Streak nudges**: `Dashboard.nudge` = {level: fresh|due|lapsed|never, days_since, headline, detail}
  computed from `last_practice_date`. Rendered as a dashboard banner with a "Practise now" CTA.
  `TeamView.lapsed_members` lists reps idle 3+ days and drives an amber banner on `/team`.
  In-app only — no email/SMS.
- **Same-prospect retry**: `POST /api/simulations/{id}/retry` clones the scenario, difficulty and mode
  (and voice persona) into a fresh simulation with a new opening line, so attempt comparison is
  apples to apples. Scorecard button: "Run this exact prospect again"; "New scenario" is separate.

---

# V5 — Staged learning path, prospect journeys, memory, hints, readiness

- **9 exercises** (added `networking`, with a full curriculum module) organised into 6 stages via
  `GET /api/stages`: foundations → starting conversations → understanding → resistance →
  real-world → commitment. Guidance only; nothing hard-locked beyond the XP difficulty tiers.
- **Prospect journeys** (`backend/lib/journeys.py`): 3 recurring characters — Marcus Webb (cold
  prospect: cold-call → objection-handling → discovery → closing), Sarah Lindqvist (networking →
  30-second commercial → discovery → in-person → closing), David Okonjo (warm walk-in: in-person →
  value statement → objection-handling → closing). One hidden dossier per character, revealed only
  through questioning. `GET /api/users/{id}/journeys` returns per-stage completion + best score;
  `POST /api/simulations` accepts `journey_id` with `mode: "journey"`.
- **Memory continuity**: on a journey stage, prior completed transcripts for that (user, journey)
  are digested into `simulation.prior_context` and injected into the prospect prompt with rules to
  call out re-asked questions ("I already told you that when you rang me") — verified live. The same
  digest goes to the evaluator, and **Relationship Memory** is now a scored category.
- **Live coaching rail**: `GET /api/simulations/{id}/hint` returns {stage, goal, example, avoid} and
  409s above Level 2. Level 1 shows example wording outright; Level 2 hides it behind
  "Show example wording". The rail renders beside the transcript and refreshes each prospect turn.
- **Customer Readiness Score**: weighted (Discovery 20, Listening/Objections/Value 15 each, then
  Closing, Next Steps, Opening, Rapport, Clarity, Confidence, Relationship Memory) — unpractised
  competencies count as zero so breadth matters. Shown on the dashboard with per-category weights
  and the biggest opportunity.
- **Voice realism**: switched to `eleven_multilingual_v2` with per-difficulty stability/style curves
  and light punctuation shaping for breaths.
