"""Private browser fixtures; MOCKED Google identities, real app/backend ownership checks."""
import asyncio
import json
import os
from pathlib import Path
import sys
import uuid
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from server import app
from lib.db import db
from lib.auth import hash_password, personal_workspace
from lib.security import digest
from models.schemas import UserProfile


async def main():
    fixtures = {}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(uuid.uuid4().hex, 12345)),
        base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        for name, has_password in [('with_password', True), ('without_password', False)]:
            nonce = uuid.uuid4().hex
            user = {**UserProfile(name='Internal recovery demo').model_dump(),
                'email': 'google-recovery-' + nonce + '@example.com', 'is_internal': True}
            if has_password:
                user['password'] = hash_password('Fixture-Link-Only-2026!')
            await db.users.insert_one(dict(user))
            await personal_workspace(user)
            flow = (await client.post('/api/auth/google/start')).json()
            code = 'controlled-recovery-' + nonce
            await db.oauth_flows.update_one({'_id': digest(flow['state'])}, {'$set': {
                'identity': {'id': 'internal-google-recovery-' + nonce, 'email': user['email'],
                    'name': 'Mocked Google name', 'email_verified': None}, 'code_hash': digest(code)}})
            fixtures[name] = {'flow': flow, 'session_id': code, 'user_id': user['id']}
    path = Path('/app/checkpoints/google-recovery-fixtures.json')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as out:
        json.dump(fixtures, out)
    print('Two private internal recovery fixtures prepared; Google identities MOCKED, no credentials printed.')


if __name__ == '__main__':
    asyncio.run(main())