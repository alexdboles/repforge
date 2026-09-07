from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4
import httpx
import pytest
from server import app
from lib.db import db
from lib.auth import hash_password, verify_password
from lib.security import digest
from lib.privacy import clean

@pytest.mark.asyncio(loop_scope='session')
async def test_recovery_one_use_revocation_expiry_and_privacy():
    uid = 'reset-test-' + uuid4().hex
    email = uid + '@example.com'
    await db.users.insert_one({'id': uid, 'email': email, 'password': hash_password('Original2026!'), 'auth_epoch': 0})
    try:
        transport = httpx.ASGITransport(app=app, client=(uid, 12345))
        async with httpx.AsyncClient(transport=transport, base_url='https://test.local', headers={'Origin': 'https://test.local'}) as c:
            with patch('routers.password_reset.recovery_configured', return_value=True), patch('routers.password_reset.send_reset', AsyncMock()) as mail:
                response = await c.post('/api/auth/forgot-password', json={'email': email})
                missing = await c.post('/api/auth/forgot-password', json={'email': 'absent-' + email})
                assert response.status_code == missing.status_code == 202
                assert response.json() == missing.json()
                mail.assert_awaited_once()
                token = mail.call_args.args[1]
                stored = await db.users.find_one({'id': uid})
                assert stored['password_reset_hash'] == digest(token)
                assert 'password_reset_hash' not in clean(stored)
                response = await c.post('/api/auth/reset-password', json={'token': token, 'password': 'Replacement2026!'})
                assert response.status_code == 200
                stored = await db.users.find_one({'id': uid})
                assert verify_password('Replacement2026!', stored['password'])
                assert stored['auth_epoch'] == 1 and 'password_reset_hash' not in stored
                assert (await c.post('/api/auth/reset-password', json={'token': token, 'password': 'Another2026!'})).status_code == 400
                await db.users.update_one({'id': uid}, {'$set': {'password_reset_hash': digest(token), 'password_reset_expires': datetime.now(timezone.utc) - timedelta(seconds=1)}})
                assert (await c.post('/api/auth/reset-password', json={'token': token, 'password': 'Another2026!'})).status_code == 400
    finally:
        await db.users.delete_one({'id': uid})

@pytest.mark.asyncio(loop_scope='session')
async def test_recovery_not_configured_and_delivery_failure():
    uid = 'reset-failure-' + uuid4().hex
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(uid, 12345)), base_url='https://test.local') as c:
        with patch('routers.password_reset.recovery_configured', return_value=False):
            assert (await c.post('/api/auth/forgot-password', json={'email': 'nobody@example.com'})).status_code == 503
    from routers.password_reset import deliver_reset
    await db.users.insert_one({'id': uid})
    try:
        with patch('routers.password_reset.send_reset', AsyncMock(side_effect=RuntimeError('fixture'))):
            await deliver_reset(uid, 'fixture@example.com')
        assert 'password_reset_hash' not in await db.users.find_one({'id': uid})
    finally:
        await db.users.delete_one({'id': uid})

async def test_readiness_failure_hides_details():
    from routers.service import readiness
    with patch('routers.service.db.command', AsyncMock(side_effect=RuntimeError('private database details'))):
        response = await readiness()
        assert response.status_code == 503 and b'private' not in response.body
