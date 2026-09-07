# GitHub maintenance review — 2026-09-07

Reviewed the private export at `f3004f4`: routes, authentication, provider boundary,
lifecycle, privacy, frontend session/voice handling, setup and regression coverage.
This is a maintenance review, not a penetration test or live deployment certification.

## Changes

- Restored environment templates; added dependency locks and a ready-to-enable GitHub checks workflow.
- Standard OpenAI SDK works without the Emergent-only package. Emergent remains optional.
  Requests preserve application budgets/timeouts, disable SDK retries and set store=False.
  This does not claim zero provider retention. See the
  [official API documentation](https://developers.openai.com/api/docs/guides/text).
- Updated the router dependency flagged by npm audit. The advisory concerned RSC mode,
  which this client-side app does not use; the affected dependency is nevertheless patched.
- Honored cookie configuration and reject insecure SameSite=None settings.
- Fixed token cleanup with blocked local storage and malformed/expired tokens.
- Detached mic callbacks before abort and reset playback state on a new request.
- Reset simulation state when switching to a different call URL.
- Lazy-loaded screens: main JavaScript entry reduced from 1,182.93 kB to about 238 kB.
  Other screens still download their own chunks when visited.
- Fixed narrow mobile demo/sample-report cards and removed unused hook dependencies.
- Made operator checkpoint paths portable and corrected local setup instructions.

## Verified locally

- Fresh public Python dependency installation succeeds without Emergent's private package.
- Build/typecheck succeeds, with no oversized-chunk warning after page splitting.
- 33 focused backend tests pass on separate MongoDB 8.0; provider outcomes are mocked.
- Five frontend session tests pass (migration, expiry, malformed data, blocked storage).
- Privacy HTTP smoke passes: export, ownership isolation, deletion and stale-session
  rejection, with direct database checks. Only disposable local fixtures were used.
- Browser guest sign-in/dashboard and missing-provider error behavior checked.
- Mobile dashboard visually checked and corrected.
- npm audit reports zero known vulnerabilities at review time.
- Python syntax/undefined-name checks pass. Heuristic source/history scan reports no
  credential-shaped strings; this does not guarantee absence of every possible secret.
- Three remaining UI-export lint warnings concern development hot refresh.

## Recommended before broader launch

1. Verify paid AI conversations/grading, ElevenLabs playback, real Google login and
   physical microphone behavior in the intended deployment. These were not tested live here.
2. Supply a verified support/privacy mailbox and operator details.
3. Choose retention periods and schedule guest-data/backup cleanup; closing a tab does
   not erase stored guest records.
4. Add self-service account recovery before broader customer onboarding.
5. Add deployment monitoring and budget alerts beyond existing request ceilings.
6. Review historical internal artifacts and choose licensing before making the repo public.

No Emergent deployment was triggered. Future Emergent exports should be merged and
reviewed rather than overwrite this maintained source.

The current GitHub token lacks workflow permission. Automation is supplied in
`docs/automation/checks.yml` and is not active until moved to `.github/workflows/checks.yml`
using an account with that permission. All reported checks above ran locally.
