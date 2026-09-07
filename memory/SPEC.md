# RepForge — Voice-First AI Sales Academy

## Privacy and data controls (current feature)
Public `/privacy`, `/terms`, `/data` describe actual storage, essential browser state,
provider boundaries, guest persistence, known Google handoff issue and absence of
billing. Profile/footer links reach real JSON export and typed-confirmation permanent
erasure. `GET /api/data/summary|export` and `DELETE /api/data/account|guest|sessions/{id}`
derive identity from the current session; deletion requires `?confirm=DELETE`.
Account/guest erasure removes owned Mongo records, linked OAuth data, generated speech,
feedback, minimal analytics and memberships without deleting another user's records.
Session erasure includes descendant retries/drills, copied prior memory, feedback and
audio. XP from deleted calls is removed and streak resets. Exports recursively omit
secrets, hashes and sign-in proofs. Activity guards prevent new writes racing erasure;
busy accounts return retryable 409. Browser storage/query cache clear only after the
server confirms erasure. Guest IDs alone never authorise access.
Existing email/password, verified workspace roles and guest flows remain; no new auth
roles or credentials are required. Distress/self-harm prompt priority overrides buyer
roleplay and excludes disclosures from coaching evidence; this is prompt-level safety,
not automatic hang-up, medical support or guaranteed detection.
Implementation, cleanup dry-runs, retention limits, failure recovery and provider sources
are documented in `/app/PRIVACY_AND_DATA.md`. No scheduled guest cleanup, provider
zero-retention claim, backup purge promise or fabricated privacy contact. Real-user
records and backups are not bulk-deleted.
Verification: tier-one gate passed clean. `yarn typecheck` passed; the public-preview
curl suite passed 17 requests plus real Mongo assertions for recursive session erasure,
legacy/current audio removal, account and guest erasure, secret-free JSON export,
cross-account denial, confirmation/type gates, in-flight exclusion and revoked sessions.
The public browser journey passed: public notices → live UI-created demo → actual JSON
download → cancel/confirm session deletion → empty History → guest erase → cleared
browser session → public mobile Data page. No console/runtime/HTTP errors in the browser
flow. Only disposable fixtures were deleted. Safety was verified structurally for prompt
priority across five difficulties; live distress response quality and physical microphone
behaviour were not tested in this privacy pass. Google identity fixtures were synthetic;
the live Google handoff remains blocked upstream. No testing-subagent escalation was
needed after this clean gate. Browser script/results: screenshot_tool_ts-20260907_163008_803.spec.ts
under `.emergent/scripts/adhoc/`; screenshots in `/root/.emergent/automation_output/20260907_163008/`.

## Emergent-managed Google sign-in
Password confusion recovery: when a legacy record matches, the UI no longer assumes
the user created or knows its stored password. Passwordless records never show a
password form; all linking users can select "I never set or don't know that password".
An authenticated, nonce-bound Google flow can save a three-day `oauth_recoveries`
request, with a non-secret reference and explicit "no email sent" disclosure. Saving
a request does not link accounts, grant permissions, reset passwords or expose history.
An authorised private operator can approve only after explicit account-owner confirmation,
using `backend/scripts/approve_google_link.py REFERENCE`. It backs up original records,
creates a provider binding and verifies account fields, memberships and transcripts stay
unchanged. Subsequent Google sign-ins then need no RepForge password. No public approve
endpoint or email-only automatic takeover path is introduced.
Follow-up verification: 11 backend tests, public recovery API negative checks, TypeScript
and 8.7-second browser approved-recovery/no-password-form flow passed. Test Google
identities were MOCKED; real records/sessions exercised. The real user explicitly
authorised connecting the matching pending identity, but that ten-minute request
expired before execution. No real-user binding has been created yet; request a fresh
Google sign-in/recovery reference before applying the authorised private action.
Google is an additional option inside the existing sign-in/signup panel; the demo stays
primary and password/guest authentication remains unchanged. The redirect is derived
from the current browser origin, returning to `/dashboard?google_state=…#session_id=…`.
Callback detection uses reactive router location before the session boundary. A
10-minute server-issued state and tab-held verifier bind initiation to the callback;
temporary fragments are immediately removed and duplicate StrictMode exchanges suppressed.
Server-only exchange uses Emergent's managed session-data endpoint. Only a trusted
explicit boolean `email_verified=true` permits automatic matching-email linking.
Because the documented provider response omits that claim, matching existing password
accounts normally confirm their RepForge password once. Subsequent sign-ins use the
stored provider identity binding. New Google accounts have isolated personal workspaces.
No existing profile, password, transcript, role, workspace or XP is replaced on linking.
`oauth_flows`/`oauth_codes` have TTLs; identity bindings are unique. Code reuse across
flows is rejected; cached completion cannot restore a session revoked by logout.
Provider session tokens are not stored or sent to the browser; RepForge's existing
HttpOnly JWT + 12-hour tab-scoped preview bearer and auth epoch are reused.
Embedded previews offer opening the app in a new tab for Google's account picker.
No new Google client secret, app deployment, provider model change or voice lifecycle
change is part of this feature. See `auth_testing.md` for the managed testing contract.
Verification: 9 backend cases passed, TypeScript passed, controlled callback/linking,
logout, guest, mobile and embedded-new-tab browser checks passed (iteration12). Real
managed site handoff returned upstream `/oauth/` and background-asset404s; a rendered
crawl still reached Google Accounts. Support confirmed upstream issue. Human real
Google consent/return remains unverified; do not call the full live flow verified.

## Hardening pass (supersedes historical entries below)
Workspace privacy uses immutable workspace IDs plus verified membership records,
never `org`. All 662 pre-existing accounts were isolated into personal workspaces
after a checksummed private BSON backup. Historical assignments are retained but
quarantined as unverified; no transcript or account was deleted.
Invites are private 48-hour codes tied to the authenticated invitee's email. Reports
and assignment writes require manager/admin/owner; guests cannot manage teams.
Sessions are server-validated. Cookie wins over expired bearer; logout revokes all
of that account's sessions via auth epoch. The 12-hour iframe bearer fallback is
migrated from localStorage to tab-scoped sessionStorage. Cache resets on logout,
account changes and cross-tab session events.
Mongo TTL counters/leases bound guests, user starts, active sessions and provider
request/character reservations. TTS accepts only an owned saved prospect turn;
mic samples use a bounded fixed-text endpoint with the session's saved voice.
Voice QA is platform-admin-only. `/api/health` is read-only; `/status` was removed.

Lifecycle: preparation → active → ending → grading → completed or grading_failed;
preparation/active may be abandoned. Activation starts the clock. Transcript writes
have stable IDs, version guards and request idempotency keys. Ending atomically
freezes the authoritative transcript; no subsequent turns can enter it. Failed
prospect requests retain accepted speech. Grading retries reuse frozen evidence.
An expiring grading lease and recovery sweep handle worker interruption. A durable
reward outbox and atomic per-user award markers prevent duplicate XP and recover
assignment completion; assignments require the exact linked exercise/difficulty.

New grading uses a strict versioned evidence rubric. Overall score is calculated
from applicable assessed categories (focus weight 2, others 1). Exact quotations
and turn indices are verified against the frozen transcript. Malformed/empty grades
fail recoverably, never become a score of zero. Missing categories are unassessed.
Legacy reports stay readable and explicitly labelled unvalidated. Text counts are
computed in code; no acoustic confidence, interruptions, vocal cues or raw-audio replay.
Full retries clone scenario/context/product/rubric/voice and link the source.
Moment drills reconstruct the exact referenced exchange, grade a targeted baseline
with the same rubric/model, and compare only that skill; ties do not improve.
Coached drills are excluded from ordinary buyer journey memory and full-call trends.
Full coached retries have a clearly labelled source-versus-retry comparison for
shared skill scores, without adding that comparison to unaided progress metrics.
Readiness separates covered skills from assessed scores; no customer certification
is claimed. Team trends use common scenario cohorts across dated 14-day UTC periods.
Dashboard totals no longer truncate at 500; history is paginated. Manager-hour
estimates have a visible adjustable assumption and exclude drills/under-two-minute calls.

Demo: primary landing CTA launches the existing Level 2 cold call, after an isolated
guest session if needed. Public `/sample-report` never creates a guest account.
Every new call includes a product/buyer/objective brief, microphone check or explicit
typed mode. Two minutes is labelled a target, not a forced limit. Mic input activity,
recognition support, skipped checks and human playback confirmation are distinct.
Optional live hints require opt-in and mark practice assisted. Product notes remain
available separately. Library direct practice is no longer gated by training pages.
Dashboard hides empty stats before a first call; personal next action precedes demo
promotions after practice. Reports have shared evidence-led coach observations,
targeted retry, contextual tagged transcript navigation and explicit text-only scope.
History supports pagination, recovery and abandoning active/preparation calls.
Reduced motion, focus outlines, visible auth/reply labels and readable print styles
are supplied. Printed sample reports retain explicit fictional sample labels.

Owner evidence: `/owner/evidence` and `/api/owner/evidence` are platform-admin-only,
not workspace-owner-accessible. `evidence_events` contains deduplicated server-authored
events, pseudonymous actor IDs and coarse exercise/difficulty/mode context only.
No transcript text, credentials, names or emails enter analytics. Fixtures/internal
users are excluded and past records are not backfilled as adoption. Date filters are
UTC and limited to 366 days. Demo completion uses a matched start cohort; return use
requires activity on distinct days. Optional report helpfulness ratings are stored
separately. No platform admin is inferred or auto-promoted; private operator command
and truthful contest narrative live in `memory/CONTEST_EVIDENCE.md`.

Portfolio preparation: root `README.md` now describes RepForge rather than a skeleton.
`PORTFOLIO_CHECKLIST.md` tracks checked A–D deliverables and remaining owner publication
decisions. Public `docs/` contains demo guide, architecture/Mermaid, validation, honest
status, read-only history audit and three real fictional-demo screenshots. No video,
licence, ownership claim, repository publication, deployment or contest change was made.
`scripts/public_release_audit.py` and `scripts/check_portfolio_docs.py` are read-only.
Private checkpoints/configuration/credentials/reports are ignored; already tracked
internal files still require manual history/export review. Production URL was readable
but older than the verified preview, explicitly documented rather than auto-deployed.

Tagline: *Practice the Conversation Before It Counts.*

## What it does
A "sales flight simulator". A rep picks an exercise + difficulty, reads a pre-call brief,
holds a live voice conversation with an AI prospect (OpenAI `gpt-5.4` when `OPENAI_API_KEY` is set,
otherwise Claude Sonnet 4.5 via the Emergent universal key), ends the call, and receives an AI scorecard with competency scores,
quoted strengths/misses, coaching priorities, communication analytics and a tagged
transcript. Progress, XP/levels/badges/streaks and history are persisted in MongoDB.

## Stack
FastAPI (`/api` router) + motor/Mongo; Vite + React 19 + TS strict + Tailwind v4 + shadcn.
Voice: browser Web Speech API (`SpeechRecognition` for mic, `speechSynthesis` for the
prospect's voice). A typed-reply input is always available as a fallback for browsers
without speech recognition (including headless Chromium in tests).

## Auth
Email + password accounts with bcrypt hashing and a signed JWT in an **httpOnly, Secure,
SameSite=Lax** cookie (`repforge_session`, 14 days). A "Continue as guest" button creates a
throwaway account for first-time visitors/judges. Routes: `POST /api/auth/signup`,
`/auth/login`, `/auth/guest`, `/auth/logout`, `GET /auth/me`. `POST /api/users` no longer
exists. The browser also caches the non-sensitive user id in localStorage
(`vocalpitch.user_id`) for UI state; identity on the server always comes from the cookie.

Authorization: every user-owned route derives the caller from the cookie and enforces
ownership (`require_self` / `require_owned` / `require_org` in `backend/lib/auth.py`). A
`user_id` in a request body is ignored. Foreign simulation ids return 404. Expensive
endpoints (TTS, turns, starts, hints, scenario generation, login) are rate limited per
user/IP, max 3 concurrent live simulations. Details in `memory/SECURITY.md`.

## Data model (Mongo)
- `users`: id, name, role, experience_level, org, xp, level, streak, last_practice_date, badges, created_at
- `simulations`: id, user_id, exercise_id/name, difficulty/name, scenario (full incl. hidden),
  status (active|analyzing|completed), transcript[{speaker,text,at}], started_at, ended_at,
  duration_seconds, evaluation, xp_awarded
- Static catalog in `backend/lib/catalog.py`: 8 exercises, 5 difficulties, 5 scenarios
  (each with `known` public intel and `hidden` intel the rep must discover), 14 skill
  categories, 8 badges.

## Key API routes (all under /api)
- GET `/exercises`, `/difficulties`, `/skills`, `/exercises/{id}/scenarios`
- POST `/auth/signup|login|guest|logout`, GET `/auth/me`
- GET/PATCH `/users/{id}`, GET `/users/{id}/dashboard`, GET `/users/{id}/simulations`
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

## Session lifecycle (privacy boundary)
`End simulation` aborts speech recognition (discarding pending finals), invalidates any
in-flight ElevenLabs TTS request and queued playback via a generation token, cancels
speech synthesis and freezes the transcript; late turn responses are discarded. The
backend claims the row atomically (`active → analyzing`) so double-clicks cannot
double-analyse or double-award XP.

## Demo path
`Try a 2-minute demo call` on the dashboard (`demo-launch-button`) starts a pre-configured
Cold Call vs Jordan Miller (scenario `crm-vp-sales`, Level 2) with no setup and jumps
straight into the voice cockpit.

## Roadmap placeholders
Training library shows non-clickable "Coming soon" cards for Zoom video calls,
screen-share demos and multi-stakeholder calls.

## Voice layer (fixed cast)
`backend/lib/voicecast.py` maps each recurring buyer to one permanent ElevenLabs
voice with per-character settings (stability / similarity / speed): Marcus Webb→Chris,
Sarah Lindqvist→Bella, David Okonjo→Eric, Jordan Miller→Adam, Alicia Reyes→Matilda,
Daniel Okafor→Brian, Priya Raghavan→Jessica, plus a dedicated coach voice (REP COACH→Alice)
that is never used for a buyer. AI-generated prospects fall back to a deterministic
persona→character voice. Difficulty only trims stability slightly — behaviour, not pitch,
makes a buyer hard. Model: `eleven_multilingual_v2`.

There is **no browser-speech fallback** in the prospect path: `useProspectVoice` surfaces
`voice-error` with a `voice-retry-button` if the approved voice fails. `GET /api/voice/cast`
verifies every voice id against ElevenLabs and powers the QA page at `/voice-cast`.
Prospect prompts include SPOKEN_RULES (1-3 sentences, contractions, no chatbot prose).

## Brand & terminology
RepForge (header, titles, metadata, footer). RepForge Academy = training library,
RepForge Coach = AI coach voice/rail, RepForge Coaching Report = scorecard,
RepForge Readiness Score = dashboard competency score, RepForge Simulations = live calls.

## Mic check (pre-call)
`frontend/src/components/MicCheck.tsx` gates every simulation: live input meter via
getUserMedia + AnalyserNode, "Test buyer audio" plays a real ElevenLabs line in the
assigned character voice, then "Start simulation" (or "Skip check"). Passing sets a
sessionStorage flag (`repforge.audio_verified`) so it is not repeated in the session.
Nothing from the check touches the transcript, scoring or character memory — the
prospect's opening line and the call timer only start after Start/Skip.

## Retry That Moment
`POST /api/simulations/{id}/retry-moment {miss_index}` (owner-only, graded calls only)
uses `lib.llm.moment_reprise` to rebuild the situation, the objective and the buyer's
line that re-opens that exact beat, and creates a new simulation with
`mode="moment"`, `retry_of`, `moment_label/situation/objective`, `origin_score`.
On completion `moment_improved` is set (retry score >= original) and
`users.moments_corrected` is incremented. The original attempt and its score are never
modified. UI: "Retry that moment" on every miss in the coaching report, a banner during
the retry call, and an original-vs-retry comparison on the retry's report.

## Sample coaching report
`/sample-report` (linked from the dashboard `sample-report-card`) is hand-authored
SAMPLE data — readiness 78, Coach's One Thing, skill breakdown, conversation metrics,
Listening IQ 86 with a missed vocal cue, clickable timeline (03:42 price objection
shows a full coaching moment + "See how Retry That Moment works"), strengths,
priorities and a recommended drill. Clearly badged as sample data.
