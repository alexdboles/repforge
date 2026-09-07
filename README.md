# RepForge

## Practice the conversation before it counts.

RepForge is an AI sales flight simulator for new and developing sales professionals.
Knowing sales theory is different from handling a real buyer. Manager-led role-play
requires another person's time; RepForge offers realistic repetitions and immediate,
conversation-specific coaching before a rep practises on customers.

**The loop:** choose a situation → review the brief → speak or type → receive
evidence-linked coaching → retry a specific moment → review separate practice history.

- **Live app:** [www.therepforge.app](https://www.therepforge.app/)
- **Updated build verified here:** [RepForge preview](https://prospect-practice.preview.emergentagent.com)
- **Release status:** [Project status](docs/PROJECT_STATUS.md) · [Validation](docs/VALIDATION.md)

The live domain was reachable during this pass but displayed the older landing page.
The improvements and screenshots below were verified on the preview. This preparation
did **not** deploy, publish a repository, push commits or modify the contest submission.

### Implemented and checked

- Guided sales exercises, five buyer difficulty levels, recurring fictional buyers and
  Practice My Business remain part of the product; the demo is a preconfigured Level 2 cold call.
- Browser speech recognition, ElevenLabs prospect playback, microphone setup, explicit
  typed mode and durable transcript storage. Human microphone/audio quality is **not**
  established by automated tests.
- Frozen-transcript grading with a strict evidence rubric; exact quote/turn validation,
  applicable skill weights, recoverable provider failures and one bounded validation repair.
- Exact-moment coached drills and clearly labelled full-retry comparisons. Coached
  attempts do not masquerade as unaided improvement; a tie is not improvement.
- Isolated personal/guest workspaces, account-email-bound invitations, manager-only
  team reports/assignments, server-verified sessions and logout revocation.
- Emergent-managed Google sign-in alongside email/password and guest access. Existing
  accounts link only with verified provider email evidence or a one-time RepForge
  password confirmation; their records and workspace permissions remain unchanged.
- Persistent history, text-derived counts, explicit skill coverage and restricted owner
  usage evidence. No invented adoption, revenue or measured manager-time savings.

See the [validation matrix](docs/VALIDATION.md) for what was exercised live, mocked,
carried forward or left for manual verification. This is not a production-security certification.

### Actual application screenshots

Captured from the updated preview using a controlled internal demo and fictional buyer/product
data. These are browser screenshots, not AI-generated mockups or customer testimonials.

![Updated RepForge landing with the two-minute demo action](docs/images/landing-demo.jpg)
*Landing page; the buyer conversation illustration is explicitly an example.*

![RepForge active simulation using a fictional demo buyer](docs/images/simulation-demo.jpg)
*Actual fictional demo call with a typed reply option and prospect playback; no personal customer data.*

![Evidence-linked coaching for a deliberately weak fictional sales demo](docs/images/coaching-demo.jpg)
*Actual AI-graded demo conversation, not a hand-authored performance claim.*

### How it was built

RepForge was built with Emergent and refined through product direction, code review,
iterative implementation and testing. Emergent supported the full-stack application,
provider integrations, persistence, UI and verification workflow. This README does not
claim the code was written entirely by hand or invent contributor/ownership details.

## Layout

```
repforge/
  backend/   FastAPI + motor (async MongoDB) + Pydantic v2 — python, /root/.venv
  frontend/  Vite + React 19 + Tailwind v4 + shadcn/ui (TypeScript strict)
  tests/     Playwright e2e workspace (pre-scaffolded)
  docs/      Demo, architecture, validation, project status and real screenshots
  scripts/   Read-only public-release audit and documentation checks
```

## Running

### Local prerequisites and dependencies

The inspected environment used Python **3.11.16**, Node **24.19.0**, Yarn **1.22.22**
and MongoDB **7.0.42**. These are observed versions, not a claim that every other version
is unsupported. Use a separate local database, never the deployed application's database.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd frontend
yarn install --frozen-lockfile
cd ..
```

The backend dependency dry-run passed in the existing environment. A completely clean
machine installation has not been executed. `emergentintegrations` uses Emergent's package
distribution and a wheel dependency; public availability and redistribution terms must
be checked before claiming a standalone installation experience outside Emergent.
The inspected pod used an additional package index; no private credentials belong in
this repository. See [validation](docs/VALIDATION.md) for the exact limits of this check.

Copy `backend/.env.example` to **private** `backend/.env` on your own machine, and set:

| Variable | Purpose |
| --- | --- |
| `MONGO_URL`, `DB_NAME` | Your separate local MongoDB and database |
| `JWT_SECRET` | A privately generated random secret of at least 32 bytes; replace the template marker |
| `CORS_ORIGINS` | Explicit allowed browser origins; local example is `http://localhost:3000` |
| `OPENAI_API_KEY` **or** `EMERGENT_LLM_KEY` | Server-only buyer/coaching provider; leave unused keys blank |
| `ELEVENLABS_API_KEY` | Server-only spoken buyer output |
| `COOKIE_SECURE`, `COOKIE_SAMESITE` | Local example uses HTTP-compatible values; HTTPS previews/production require a secure policy |
| `TRUSTED_PROXY_CIDRS` | Leave empty unless the actual trusted proxy boundary is known |
| `DAILY_LLM_REQUEST_LIMIT`, `DAILY_TTS_CHARACTER_LIMIT` | Shared reservation caps, not exact dollar budgets |

Never paste credentials into chat, README files, screenshots or test output. There are
no required frontend environment variables: `frontend/.env.example` is intentionally empty.
The browser always calls relative `/api` paths; never put provider keys in `VITE_*` values.

Start your own MongoDB using your OS's supported service procedure, then run:

Two separate processes, managed by supervisor in the pod (see "Pod conventions"
below); to run them by hand from two terminals instead:

```bash
cd backend && uvicorn server:app --host 0.0.0.0 --port 8001 --reload   # http://localhost:8001
cd frontend && yarn dev                                                # http://localhost:3000
```

## The `/api` proxy convention

Every backend route lives under `/api` (the backend mounts one
`APIRouter(prefix="/api")`), and the frontend dev server
(`frontend/vite.config.ts`) proxies `/api/*` to `http://localhost:8001`. So
frontend code always calls a **relative** path — `apiGet("/health")` →
`/api/health` — and never an absolute backend URL. The same code works in dev
(via the Vite proxy) and in production (once both are served behind a single
origin).

## Backend

FastAPI, async throughout. `python` is the app venv interpreter
(`/root/.venv/bin/python`); backend deps are pip-installed from
`backend/requirements.txt`.

- **Entry point**: `backend/server.py` — creates `app = FastAPI()`, creates
  `api_router = APIRouter(prefix="/api")`, registers routes **on the router**,
  and calls `app.include_router(api_router)` at the bottom. CORS middleware is
  added from `CORS_ORIGINS`. Never hang a route directly off `app` — it would
  land outside `/api` and the Vite proxy would not reach it.
- **The route pattern** (see `backend/routers/evidence.py`):
  1. a Pydantic model per request body and per response
    (`FeedbackRequest` / `FeedbackResponse`);
  2. an `async def` handler decorated with
    `@router.post("/feedback", response_model=FeedbackResponse)`;
  3. `await` the motor call inside it.
  FastAPI validates the request against the Pydantic model before your handler
  runs — a malformed body never reaches your code, it gets an automatic `422`
  with a `{"detail": [...]}` body.
- **Growing the backend**: as `server.py` gets crowded, move models to
  `backend/models/` and routers to `backend/routers/` (one module per resource,
  each exporting its own `APIRouter`, folded into `api_router` from `server.py`.
  Keep `app.include_router(api_router)` last; do not register API handlers directly on `app`.
- **MongoDB**: import the shared handle — `from lib.db import client, db`
  (`backend/lib/db.py` self-loads `.env` before reading env). Use it from
  `server.py`, every router, and standalone scripts like `seed.py`; never
  construct another `AsyncIOMotorClient`. Collections are attributes:
  `await db.simulations.find_one({"id": sim_id})`; authenticate and verify ownership before returning data.
  Motor connects lazily, so importing `server` never blocks on Mongo. `pymongo`
  is installed too if you need a sync client in a script.
- **Ids**: documents use a string `id` (`uuid4`) field, not Mongo's `ObjectId`
  — `ObjectId` is not JSON-serializable and leaks into response bodies. Keep the
  `uuid4` default-factory pattern from `Simulation`.
- **Config**: `backend/.env` — `MONGO_URL` (connection string), `DB_NAME`
  (database name), `CORS_ORIGINS`. `server.py` loads it with `python-dotenv`
  above its local imports, and `lib/db.py` self-loads it so standalone scripts
  inherit it too. The pod runs `mongod` locally, so `MONGO_URL` points at
  `localhost`. Add new secrets/config here; read them with `os.environ`.
- **Dates**: `backend/lib/dates.py` — `today_iso(tz=None)`. The pod clock is
  UTC; anchor "today" server-side with this, never with client-side date math.
- **Interactive check**: `cd /app/backend && python -c 'import server'` catches
  syntax/import errors without waiting for the supervisor log.

## Frontend

- Vite + React 19 + TypeScript strict, dev server on port `3000`.
- Tailwind CSS v4 (via the `@tailwindcss/vite` plugin — no separate
  `tailwind.config.js` needed) + shadcn/ui, initialized with the `base-nova`
  style and `neutral` base color, `@` path alias (`@/*` → `src/*`) wired in both
  `tsconfig.app.json`/`tsconfig.json` and `vite.config.ts`.
- `react-router-dom` and `motion` are installed. `src/App.tsx` contains routes and
  the session boundary; screens live in `src/pages/*.tsx` and are imported as
  `@/pages/<Name>`. Add
  a `<Route>` for every page you write, in the same edit that creates the page — a
  page with no route is unreachable, and any URL without a matching `<Route>` renders a
  **blank page** — `<Routes>` matches nothing and mounts nothing.
- Components installed under `src/components/ui/`: button, card, input, label,
  select, dialog, sheet, tabs, badge, calendar, sonner, textarea, table, popover,
  dropdown-menu, checkbox. Add more with `npx shadcn@latest add <component>`.
- `src/lib/api.ts` — the typed fetch layer: `apiGet<T>`, `apiPost<T>`,
  `apiPut<T>`, `apiPatch<T>`, `apiDelete<T>`, all relative to base `/api`,
  throwing `ApiError` (with `status` and the parsed body) on any non-2xx.
  **Nothing infers across the Python boundary** — you declare the response type
  yourself as a TS interface mirroring the endpoint's Pydantic model, and keeping
  the two in sync is a manual discipline. When you change a Pydantic model,
  change its TS interface in the same edit.
- `src/pages/Dashboard.tsx` demonstrates TanStack Query data fetching. Public landing
  and sample-report pages do not require a session. Protected pages verify the session
  on the server. `apiGet<T>` is a TypeScript assertion, not runtime response validation.

## TypeScript

`frontend/tsconfig.app.json` / `tsconfig.node.json` have `strict: true`. In the
pod:

```bash
cd frontend && yarn typecheck
```

— plain `tsc --noEmit` run from `frontend/` checks ZERO files (root tsconfig uses
project references with `"files": []`) and exits 0 even with type errors. Always
use `-b` for the frontend. Lint with `cd frontend && yarn lint` (oxlint).

## Data fetching

TanStack Query is wired: `QueryClientProvider` in `src/main.tsx`. Use
`useQuery`/`useMutation`, not
fetch-in-`useEffect`.

## Completion gate (tier 1)

When the build is complete, run tier 1 once, all in the same turn: a curl smoke
over the key `/api` endpoints (assert status AND a response field, plus one
negative case), `cd frontend && yarn typecheck`, and ONE happy-path browser pass
through the core user journey. Clean on all three → finish; any failure is a real
bug — fix it, re-run the failed check, and escalate to the testing subagent.
No routine typecheck/lint/smoke passes during the build — tier 1 runs exactly once.


## Testing

Two lanes.

**Backend (pytest)** — specs in `backend/tests/` as `test_*.py`, run with:

```bash
cd backend
python -m pytest -q tests/test_hardening_*.py
```

This focused suite uses controlled accounts and **MOCKED provider outcomes**. It needs
your configured local MongoDB. Never run it against a customer database. The broader
legacy `test_tscheck_*` suite includes live API/provider flows, is not the default
portfolio check, can consume credits and was not certified as a complete clean suite.

Frontend commands actually exercised in this project:

```bash
cd frontend
yarn typecheck
yarn vite build
yarn lint
```

Read-only release hygiene check from the repository root:

```bash
python scripts/public_release_audit.py
python scripts/check_portfolio_docs.py
```

`backend/pytest.ini` is canonical: `addopts = -n 2 --dist loadscope` (pytest-xdist,
already parallel — do not pass your own `-n`) and `asyncio_mode = auto` (so
`async def test_...` needs no marker). Serial is `-n 0`, **never**
`-p no:xdist` (that errors, because `addopts` still passes `-n`/`--dist`).
`backend/tests/conftest.py` is pre-scaffolded — a sync `client` fixture
(`httpx.Client` rooted at `/api`), an async `aclient`, and an `api_url()` helper,
all pointed at `BACKEND_URL` (default `http://localhost:8001`). Tests hit the
live uvicorn process, so the app under test is the one the browser sees. Add
app-specific fixtures below the marker; do not re-create the file.

**Frontend (Playwright)** — `/app/tests/` is pre-scaffolded:
`playwright.config.ts` (canonical — edit the marked lines only),
`fixtures/helpers.ts`, and a `package.json` that resolves
`@playwright/test@1.62.0` (node_modules baked into the image). Write specs into
`tests/e2e/`. Do NOT re-create the config/helpers or install/upgrade playwright —
matching Chromium browsers live at `/pw-browsers`.

The backend lane is pytest: this template's backend is Python, so `vitest` does
not apply to it.

## Pod conventions

This template runs under supervisord in the Emergent agent pod — supersedes any
local-run instructions above.

- Backend, frontend, and `mongod` are supervisor programs in Emergent. Ordinary code
  edits hot-reload. Only after dependency or environment changes, restart and poll:

  ```bash
  sudo supervisorctl restart frontend backend
  until curl -sf -o /dev/null http://localhost:3000; do sleep 2; done
  ```

- Status, only after a restart you triggered:
  `sudo supervisorctl status frontend backend`. Logs:
  `/var/log/supervisor/backend.err.log`, `backend.out.log`,
  `frontend.err.log`.
- App in a browser: the pod's preview URL (frontend, port `3000`). Backend API
  directly at port `8001`.
- `mongod` runs locally in the pod (`--bind_ip_all`); `MONGO_URL` in
  `backend/.env` points at `localhost`, no separate Mongo container.
- Both dev servers hot-reload on file edits (uvicorn `--reload` for the backend,
  Vite HMR for the frontend); no rebuild step needed for normal iteration. A
  restart is still needed after changing `.env`, `requirements.txt`, or
  `vite.config.ts`.

## Portfolio release and licensing

Use [PORTFOLIO_CHECKLIST.md](PORTFOLIO_CHECKLIST.md) before any public release.
Ignored files already tracked in Git remain in its history; internal reports and
platform files need manual review. No Git publication or history rewrite was performed.
No project licence or ownership declaration has been invented. The owner must choose
licensing and review dependency, font, provider and voice usage terms before publication.
