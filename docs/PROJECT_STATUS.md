> Historical Emergent notes below. Latest checks: [GitHub review](GITHUB_REVIEW.md).

# RepForge project status

## Implemented and verified within the documented scope

The updated preview has a working demo, typed/voice setup, AI-buyer conversation,
frozen-transcript coaching, exact-moment practice and labelled full-retry comparisons.
New workspace authorization, session revocation, paid-resource controls and strict
grading have focused regression coverage. The final focused suite passed 21 tests;
the previously failing full-retry comparison passed its public browser recheck.

Public sample reports are fictional and read-only. Real report quotations reference
saved evidence. Text counts are distinct from AI interpretations and unassessed audio
features. History pagination and abandoning active preparations are available.

Guided training, Practice My Business, recurring buyers and catalog voices were retained.
Their presence is not a claim that every possible scenario/provider combination was
newly tested. See [VALIDATION.md](VALIDATION.md) for exact coverage and prior-run context.

## Known limitations / operator decisions

- Managed Google sign-in is integrated as an additional option. Real Google account
  selection/consent still needs human verification; provider identity responses in
  automated backend tests are MOCKED. The managed service's documented response lacks
  an explicit verified-email claim, so first-time linking to an existing password
  account may require its RepForge password once. No Google password is requested by RepForge.
- Users who never set or do not know that password can request an account connection
  using a non-secret reference. Requests do not grant access automatically or send email;
  an authorised operator must verify and approve the connection. No-password records
  skip the password form entirely. This preserves older records without an email-only
  ownership bypass or silently creating a duplicate account.
- The managed auth provider's `/oauth/` page and one asset returned HTTP404 during live
  handoff checks. Support identified this as upstream; a rendered crawl could still
  reach Google Accounts. App-owned callback/linking checks pass, but a clean real Google
  consent/return journey is not yet verified. No guessed alternative endpoint was used.

- The live portfolio domain was reachable but still displayed the older build. Updated
  production behaviour is not verified and no deployment was changed.
- No independent email verification, automatic invite delivery, password recovery UI,
  MFA or per-device session-management UI is claimed. Invitations use privately shared
  expiring codes plus matching authenticated account email.
- Voice depends on browser speech recognition, permission/network conditions and a paid
  ElevenLabs service. It is not full-duplex telephony, audio recording or audio replay.
- AI may return invalid output. A single bounded repair is allowed, then grading fails
  recoverably; users may need to retry. Historical scores remain labelled unvalidated.
- Prompt instructions are separated from data, but robust adversarial security is not
  certified. Do not supply confidential customer data.
- Some analytics still process complete histories in application memory; 550-record
  correctness tests are not a high-scale load test.
- Owner evidence requires an operator to authorize a verified account; personal workspace
  owners cannot inspect global usage. No global admin was automatically created.
- A large JavaScript bundle advisory and seven release-gate lint warnings remain.
- Real audio quality, complete accessibility/print review, cross-device/browser parity,
  restore drills and broader distributed-failure tests remain manual/extended work.
- A clean standalone installation outside Emergent still needs verification of the
  Emergent integration package distribution and related provider terms.

## Estimates, not measured impact

- Two-minute demo: a target, not an enforced duration or a latency guarantee.
- Practice/readiness scores: AI assessments and skill coverage, not a validated
  qualification to handle real customers.
- Manager hours: adjustable estimate based on qualifying full calls and assumed minutes,
  not measured savings. Short drills are excluded.
- Request/character budgets: conservative provider-usage reservations, not exact spend.
- Migration record counts and test accounts: not users acquired, customers or adoption.

No revenue, testimonials, customer adoption or realised business impact is invented.
New owner evidence reports observed instrumented usage only; it does not backfill history
as a growth claim or turn scores into revenue forecasts.

## Future work, not shipped claims

Verified email/invite delivery, stronger device/session controls, richer audio timing
only if genuinely instrumented, deeper calibrated rubrics, accessibility validation,
large-history aggregation/load testing and independently validated business outcomes.
Practice bookmarks and focused drill collections are possible enhancements, not
features represented as already available.

## Portfolio publication status

Documentation/assets are prepared and checked, not published. Public-file/history findings
are tracked in [PUBLIC_RELEASE_AUDIT.md](PUBLIC_RELEASE_AUDIT.md). Already tracked
internal reports/platform artifacts require owner review even after `.gitignore` changes.
No arbitrary licence or ownership statement has been added. The owner must decide
licensing and approve the exact export/history before any public repository release.