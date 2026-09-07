"""Test-only helper: inject a MOCKED managed-provider identity into an already
real, backend-issued oauth_flows record (created via a real POST /auth/google/start).

This mocks only the provider boundary (the outbound call to Google's session-data
endpoint) at the exact seam routers/google_auth.py already supports (a flow with
`identity` pre-set skips exchange_managed_identity entirely). Everything else -
state/verifier validation, resolve_google_user, cookie issuance, auth_epoch - runs
for real against the real running server. No network calls to Google are made.

Usage: python -m tests.helpers_google_flow_inject <state> <email> <name> <email_verified true|false|none>
Prints nothing sensitive; only exits 0/1.
"""
import sys
import asyncio
sys.path.insert(0, __file__.rsplit('/backend/', 1)[0] + '/backend')
from lib.db import db
from lib.security import digest


async def main():
    state, email, name, verified_raw = sys.argv[1:5]
    verified = {'true': True, 'false': False, 'none': None}[verified_raw]
    identity = {'id': 'tscheck-google-' + digest(state)[:16], 'email': email, 'name': name, 'email_verified': verified}
    result = await db.oauth_flows.update_one({'_id': digest(state)}, {'$set': {'identity': identity}})
    if result.matched_count != 1:
        raise SystemExit('No matching pending oauth flow for this state; call /auth/google/start first')


if __name__ == '__main__':
    asyncio.run(main())
