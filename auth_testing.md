# Emergent managed Google auth — RepForge test adaptation

Managed flow supplied by the integration playbook:
1. Derive the callback from `window.location.origin`, never environment-host fallbacks.
2. Navigate to `https://auth.emergentagent.com/?redirect=<encoded callback>`.
3. Read returned `#session_id=...` before any protected-page `/auth/me` request.
4. Exchange ONLY on the backend: GET
   `https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data`,
   header `X-Session-ID`. Documented response: id, email, name, picture, session_token.
5. Establish the application's session, remove the temporary fragment, then navigate
   to the dashboard. Prevent duplicate exchange under React StrictMode.

RepForge already uses UUID `users.id`, HttpOnly JWT cookies, short-lived iframe bearer
fallback and auth-epoch revocation. Reuse those; do not create a competing auth stack,
rename user IDs or assume a cached ID proves authentication. Preserve memberships.
The documented managed response does not include an explicit email_verified claim;
safe linking must not infer verification from browser-supplied email or a domain string.

Test with controlled internal identities and MOCKED managed exchange responses, not
real Google passwords or forged live provider credentials. Cover callback state,
expiry/replay/duplicate requests, existing-account linking, isolated new workspaces,
no domain-derived membership/admin, logout, expired bearer + valid cookie, and old
password/guest paths. No raw tokens in logs, reports, screenshots or public files.

Public browser gate must check the real Google button and managed redirect. An actual
Google account-picker/consent completion requires a human's Google session; report
that boundary honestly. Browser callback processing can separately use a controlled
MOCKED API response while backend linking/session assertions run against test data.

Test identities/roles (not Google passwords) belong in private
`memory/test_credentials.md`. Clean only records created by the test. No global rate
limit resets, live user deletion, pytest.ini edits or repeated paid-provider runs.