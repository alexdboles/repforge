# RepForge verification record

## Managed Google sign-in addition — 2026-09-07 UTC

### Follow-up: user never set / does not know a RepForge password

The user reproduced a real existing-account linking dead end. An older matching record
had a stored password hash, but the user did not have a password to enter. The UI now
offers account-connection help instead of assuming that stored hash is a known password;
records with no password never display a password field. Requests require the completed
Google flow's nonce proof, persist for three days and do not authenticate or link anyone
by themselves. A private operator can connect the identity only after explicit owner
approval, with a checksummed backup and before/after account, membership and transcript checks.

Follow-up checks: **11 backend cases passed (6.26 s)**, public API recovery-boundary smoke
passed, TypeScript passed (1.69 s), browser recovery/approved-connection/no-password-form
checks passed (8.7 s, zero app errors). Google identities in these automated checks were
**MOCKED**; real app/DB/session behavior was exercised. No existing password was reset.
The user's original short-lived Google flow expired before approval, so their actual
connection still needs a fresh sign-in/recovery reference; it has not been claimed complete.

- `yarn typecheck` passed (1.95 s) for this addition.
- Public ingress API smoke passed Google initiation/proof rejection, existing password
  login, real application session validation and protected dashboard access.
- Focused managed-auth + workspace-security suite: **9 passed**, final retest 4.92 s.
  External Google identity responses are **MOCKED**; app sessions, linking and Mongo
  authorization paths are real. No Google passwords or user API keys were requested.
- Browser callback/logout/guest regression passed (17.1 s, zero app errors).
- Testing iteration 12 added two passing named browser checks: Google alongside both
  auth tabs at 390×844 plus same-origin new-tab handling; callback once under StrictMode,
  temporary URL cleanup, actual backend session, one-time existing-password linking,
  incorrect-password recovery, preserved profile and logout revocation.
- **Live provider limitation:** the documented managed-auth URL redirected to `/oauth/`
  returning HTTP 404; its background asset also returned 404. Independent curl reproduced
  this and Emergent support identified an upstream platform issue. A rendered crawl
  reached Google Accounts despite those errors. No real Google account selection/consent
  or final live identity exchange is claimed. A human test/platform confirmation remains.
- The first screenshot harness also raced reading the start response with navigation;
  the corrected controlled-boundary test passed. This was not a production callback defect.
- Existing preview configuration permits the public origin. Localhost-only browser POSTs
  require an explicit localhost `CORS_ORIGINS` entry, as in the local environment example;
  this pass did not change private configuration or deployment.

The managed provider's documented schema has no `email_verified` claim. Automatic
existing-email linking therefore requires explicit trusted boolean verification when
available; otherwise a one-time **RepForge** password confirms the existing account.
Google passwords are never collected by RepForge. This security fallback is intentional.

Prepared from actual tool/test results on **2026-09-07 UTC**. This is a bounded engineering
verification record, not certification that every possible browser, device or deployment works.

## Environment and endpoints

- Python 3.11.16, Node 24.19.0, Yarn 1.22.22, MongoDB 7.0.42.
- Updated app tested through **https://prospect-practice.preview.emergentagent.com**.
- https://www.therepforge.app/ was read-only checked and reachable, but showed older
  landing copy. Production parity is **not verified**; no deployment was performed.
- Existing accounts, configured integrations, submission and records were preserved.

## Actual outcomes

| Check | Actual result | Scope/limitation |
| --- | --- | --- |
| Public API smoke via curl | Passed | Health/catalog, login/me, dashboard/team, voice configuration; negative ownership and removed status endpoint |
| `cd frontend && yarn typecheck` | Passed | Release-gate run; later small comparison/UI changes were browser-tested, not a second claimed typecheck |
| `cd frontend && yarn vite build` | Passed | Release-gate build; advisory for a large frontend chunk |
| `cd frontend && yarn lint` | 0 errors, 7 warnings | Release-gate run; remaining unused-variable/hook-dependency warnings require considered review, not blind dependency changes |
| `python -m pip check` | Passed | No broken requirements in installed environment |
| `cd frontend && yarn check --integrity` | Passed | Installed dependency folder in sync; `--frozen-lockfile` option verified from command help, no reinstall |
| `python -m pip install --dry-run -r backend/requirements.txt` | Passed | Existing environment; no packages installed or restarted; not a clean-machine proof |
| Focused `python -m pytest -q tests/test_hardening_*.py` | **21 passed** | Final testing-agent retest, 3.41 s; controlled accounts and **MOCKED providers** |
| Live demo voice sample + two typed buyer turns | Exercised successfully | Real configured ElevenLabs sample generated/started; no human listening claim |
| Frozen grading recovery + report → exact moment retry → targeted report | Passed | Public browser recheck 25.3 s, zero console/network errors; targeted tie correctly not improvement |
| Full coached-source comparison | Passed | Public API: paired results/shared skill deltas. Main browser recheck 4.7 s, no errors; testing-agent GET-only recheck passed |
| Public fictional sample | Passed browser check | No account/guest creation required; removed unsupported replay/Listening IQ claims |
| Mobile 390×844 | Passed focused browser check | Landing/sample, compact navigation and History reachable; not an exhaustive mobile-device matrix |
| Slow-audio end/navigation and mic lifecycle | Passed focused browser rechecks | Controlled delay/lifecycle cases, not all physical-device failure modes |
| Portfolio audit | See [PUBLIC_RELEASE_AUDIT.md](PUBLIC_RELEASE_AUDIT.md) | Read-only working-tree plus available-history scan; heuristic, not a guarantee |
| `python scripts/check_portfolio_docs.py` | Passed | 12 required artifacts, local links, Mermaid block, provider placeholders and JPEG integrity |
| Screenshot content review | Completed | Three actual fictional-demo captures, no EXIF fields or visible secrets/private customer details; small-text/cropping limitations noted |

Internal raw reports remain private. The final focused testing report was iteration 11:
7 reported acceptance checks, 0 failed/blocked/test errors; five browser results were
explicitly carried forward from iteration 10 rather than billed/re-executed. Do not turn
that into a claim of seven newly executed complete end-to-end runs.

## Defects actually found and addressed

1. **Grading contract mismatch:** the provider initially used descriptive priority labels
   while validation required exact category references. The prompt was aligned; one
   bounded validation-repair attempt was added without relaxing validation. Two failed
   frozen test calls were recovered via public API 200; transcript versions stayed fixed.
2. **Coached comparison gap:** strict separation of assistance settings initially hid the
   full-retry panel. A separate labelled source-versus-coached comparison restored shared
   skill deltas while leaving unaided progress untouched. API and browser rechecks passed.
3. **Test-harness issues:** stale auth selectors and one test expecting an email field not
   returned by UserProfile were corrected. Test peer buckets are isolated; production
   rate-limit records are not reset by the final focused suite.

A broader legacy run reported 51 passes and one live grading failure, and a subsequent
attempt was rate-limit-blocked. That entire legacy suite is **not claimed as passing**.
The final retest intentionally limited scope to focused hardening tests and the remaining
browser failure to avoid additional paid-provider usage.

## What the focused backend suite covers

- Four isolated account/guest workspaces; same-name spoofing denied; invitation recipient,
  role and assignment boundaries; authenticated assigner identity; owner-only evidence.
- Valid-cookie/expired-bearer precedence, logout revocation, origin protection, UTF-8
  password limits, shared budgets and conflicting leases.
- Durable accepted speech, duplicate-turn idempotency, ending during a pending turn,
  exact frozen transcript, exactly-once XP and interrupted grading recovery.
- Malformed grades, string booleans/numbers, invalid quotes/indices/tags/recommendations,
  forbidden text-only acoustic confidence, true zero scores and bounded validation repair.
- Lexical metrics, unassessed coverage, UTC yesterday wording, 550-session totals/latest
  result, order-independent team calculation and coached-source comparisons.
- Honest sample/demo code contracts, minimal deduplicated evidence events and owned feedback.

## Migration and recovery

A recoverable source bundle/working-tree checkpoint and checksummed private BSON backup
preceded the additive migration. The backed-up dataset contained **662 accounts, 360
simulations and two assignments**—these are database migration counts, **not adoption**.
Each uncertain legacy account was isolated; matching old organisation names did not
establish colleague membership. Historical assignments were retained as unverified.
No account/transcript deletion or automatic account merging occurred.

The restore script verifies backup checksums and replaces backed-up records without
deleting newer records. A complete disaster-recovery restore drill was **not** performed.
The backups contain sensitive data and must never enter a public repository.

## Manual verification still needed

- Listen to real microphone and ElevenLabs playback on intended devices; confirm
  pronunciation, intelligibility, echo, headset switching and end-to-end latency.
- Test real denied/late permission prompts, intermittent networks, autoplay policies,
  alternative browsers and iframe cookie restrictions on the actual production deployment.
- Inspect print/PDF output visually and with assistive technology. Print CSS and labels
  exist; a full accessibility/print audit is not claimed.
- Adversarial prompt red-teaming: instruction separation is implemented, but complete
  resistance to score manipulation/hidden-information elicitation is not proven.
- High-volume performance, distributed failure stress and complete assignment/outbox
  crash recovery need extended testing beyond the focused assertions.
- Grant platform owner access only after verifying the intended account. No administrator
  was inferred from display names, organisation labels or contest participation.
- Re-run type/build/lint and focused tests on the exact reviewed public export before
  publication; no automatic publication or history rewriting is part of this pass.