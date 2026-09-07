"""Private controlled browser fixture. No live Google credentials or provider calls.
MOCKED provider identity passes through real RepForge exchange and session issuance.
The output file is private/ignored and contains a short-lived app test session.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import uuid
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from server import app
from lib.db import db
from models.google_auth import ManagedGoogleIdentity


async def main():
    nonce = uuid.uuid4().hex
    identity = ManagedGoogleIdentity(id='internal-google-browser-' + nonce,
        email=f'google-browser-{nonce}@example.com', name='Internal Google Demo', email_verified=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(nonce, 12345)),
        base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        flow = (await client.post('/api/auth/google/start')).json()
        with patch('routers.google_auth.exchange_managed_identity', AsyncMock(return_value=identity)):
            result = await client.post('/api/auth/google/exchange', json={
                'state': flow['state'], 'verifier': flow['verifier'], 'session_id': 'controlled-browser-code-' + nonce})
        assert result.status_code == 200
        payload = result.json()
        await db.users.update_one({'id': payload['session']['user']['id']}, {'$set': {'is_internal': True}})
        output = (Path(__file__).resolve().parents[2] / 'checkpoints' / 'google-browser-fixture.json')
        output.parent.mkdir(mode=0o700, exist_ok=True)
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(payload, stream)
        print('Private internal Google browser fixture prepared; provider identity MOCKED. No credentials printed.')


if __name__ == '__main__':
    asyncio.run(main())