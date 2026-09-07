# Activate recovery, contacts and monitoring

These features are implemented in source. They are not automatically deployed by a GitHub push.

## Details needed from the owner

- Public operator/person or business name.
- Verified support and privacy contact addresses (one address may serve both).
- An email provider with authenticated SMTP STARTTLS on port 587 and a verified sender/domain.
- Destination for uptime alerts and an uptime-monitoring account.
- GitHub workflow permission is configured; automated checks are enabled.

Never put SMTP credentials, provider keys or reset links in GitHub or chat.

## Deployment secrets/settings

Set `PUBLIC_OPERATOR_NAME`, `PUBLIC_SUPPORT_EMAIL`, `PUBLIC_PRIVACY_EMAIL`.
The `/support` page and privacy page use these values from `/api/site-info`.
Only these intended public fields are returned; SMTP settings remain private.

Configure `PUBLIC_APP_URL` to the canonical HTTPS app origin, `SMTP_HOST`,
`SMTP_PORT=587`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `MAIL_FROM`.
Verify the sender domain with the chosen mail provider. Recovery stays unavailable
until these settings are present. Actual deliverability must be tested after deployment.

Reset requests use a generic response, per-address and per-client limits, a hashed
30-minute proof, one-use atomic consumption and revocation of earlier sessions.
Links carry the proof in a fragment, not a server query string. Do not enable email
click tracking or URL rewriting for reset messages. Reset proofs are excluded from exports.
No reset email is sent during the automated tests; delivery is mocked.

## Monitoring

Point an external HTTPS uptime monitor at `/api/ready` on the deployed origin.
Expect HTTP 200 and `{"status":"ready"}`. A failed or timed-out database ping
returns 503 without database details. This is readiness monitoring, not a paid
AI/provider quality test. Alert destination and scheduling belong in the external monitor.

Alternatively run `python scripts/check_readiness.py https://www.therepforge.app`
from your own monitor/scheduler; exit 1 means failure. Do not schedule this against
the live domain until the endpoint has been deployed. No background schedule was created here.

## GitHub checks

The active workflow is `.github/workflows/checks.yml`. It runs build, lint, frontend
tests and 36 focused backend tests with a disposable MongoDB service, without provider keys.

## Final deployment checks

- Request a reset for a controlled account and confirm actual email arrival.
- Follow the link, change the password, verify the old password and prior sessions fail.
- Confirm a second use and an expired link fail.
- Check the public contact addresses and monitor outage notification delivery.
- Verify real Google login and AI/audio separately; none is proven by a readiness ping.
