"""Managed Google contract tests: external identities are MOCKED, app auth is real.
Use the configured isolated test database; never run against a customer database.
"""
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import AsyncMock, patch
import httpx
import pytest
from fastapi import HTTPException
from lib.db import db
from lib.auth import hash_password, verify_password
from lib.security import digest, ensure_indexes
from lib.google_auth import exchange_managed_identity
from models.google_auth import ManagedGoogleIdentity
from server import app

pytestmark = pytest.mark.asyncio(loop_scope='session')


async def test_google_new_user_replay_logout_and_isolated_workspace():
    prefix = 'google-' + uuid.uuid4().hex
    identity = ManagedGoogleIdentity(id=prefix, email=f'{prefix}@example.com', name='Internal Google fixture')
    ids, flows, codes = [], [], []
    await ensure_indexes()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(prefix, 12345)),
        base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        try:
            flow = (await client.post('/api/auth/google/start')).json(); flows.append(digest(flow['state']))
            assert len(flow['verifier']) >= 32 and flow['expires_at']
            proof = {k: flow[k] for k in ('state', 'verifier')}
            code = prefix + '-opaque'; codes.append(digest(code))
            payload = {**proof, 'session_id': code}
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock(return_value=identity)) as provider:
                bad = await client.post('/api/auth/google/exchange', json={**payload, 'verifier': 'x' * 43})
                assert bad.status_code == 400 and provider.await_count == 0
                first = await client.post('/api/auth/google/exchange', json=payload)
                assert first.status_code == 200, first.text
                data = first.json(); uid = data['session']['user']['id']; ids.append(uid)
                await db.users.update_one({'id': uid}, {'$set': {'is_internal': True}})
                assert data['status'] == 'authenticated'
                assert data['session']['user']['workspace_id'] and data['session']['user']['is_admin'] is False
                assert 'HttpOnly' in first.headers['set-cookie']
                repeated = await client.post('/api/auth/google/exchange', json=payload)
                assert repeated.json()['session']['user']['id'] == uid and provider.await_count == 1
                assert await db.users.count_documents({'email': str(identity.email)}) == 1
                assert await db.memberships.count_documents({'user_id': uid}) == 1
                assert (await client.get('/api/auth/me')).json()['id'] == uid
                # Real fallback bearer remains useful even with no cookies.
                client.cookies.clear(); client.headers['Authorization'] = 'Bearer ' + data['session']['token']
                assert (await client.get('/api/auth/me')).json()['id'] == uid
                assert (await client.post('/api/auth/logout')).status_code == 200
                client.cookies.clear()
                assert (await client.get('/api/auth/me')).status_code == 401
                assert (await client.post('/api/auth/google/exchange', json=payload)).status_code == 400
                other = (await client.post('/api/auth/google/start')).json(); flows.append(digest(other['state']))
                replay = await client.post('/api/auth/google/exchange', json={
                    'state': other['state'], 'verifier': other['verifier'], 'session_id': code})
                assert replay.status_code == 400 and provider.await_count == 1
            # A new Google identity with the same display name gets a different workspace.
            other_identity = identity.model_copy(update={'id': prefix+'-second', 'email': f'{prefix}-second@example.com'})
            other = (await client.post('/api/auth/google/start')).json(); flows.append(digest(other['state']))
            new_code = prefix + '-second-code'; codes.append(digest(new_code))
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock(return_value=other_identity)):
                client.headers.pop('Authorization', None)
                response = await client.post('/api/auth/google/exchange', json={
                    'state': other['state'], 'verifier': other['verifier'], 'session_id': new_code})
                second = response.json()['session']; ids.append(second['user']['id'])
                assert second['user']['workspace_id'] != data['session']['user']['workspace_id']
                assert (await client.get('/api/users/'+uid+'/dashboard')).status_code == 403
                assert (await client.get('/api/teams/'+data['session']['user']['workspace_id'])).status_code == 403
        finally:
            await cleanup(ids, flows, codes)


@pytest.mark.parametrize('verified', [True, None])
async def test_google_links_existing_without_changing_records_or_roles(verified):
    prefix = 'google-link-' + uuid.uuid4().hex
    uid, wid, sid = prefix + '-user', prefix + '-workspace', prefix + '-simulation'
    email = prefix + '@example.com'
    password = 'Fixture-Link-Only-2026!'
    hashed = hash_password(password)
    await db.users.insert_one({'id': uid, 'name': 'Existing fixture', 'email': email, 'password': hashed,
        'is_internal': True, 'org': 'Existing team', 'workspace_id': wid, 'role': 'Sales Professional', 'xp': 125})
    await db.memberships.insert_one({'workspace_id': wid, 'user_id': uid, 'role': 'member', 'verified': True})
    await db.simulations.insert_one({'id': sid, 'user_id': uid, 'transcript': [{'speaker': 'rep', 'text': 'Fictional prior practice'}]})
    identity = ManagedGoogleIdentity(id=prefix, email=email, name='Different Google name', email_verified=verified)
    flows, codes = [], []
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(prefix, 12345)),
        base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        try:
            flow = (await client.post('/api/auth/google/start')).json(); flows.append(digest(flow['state']))
            proof = {k: flow[k] for k in ('state', 'verifier')}
            code = prefix + '-opaque'; codes.append(digest(code))
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock(return_value=identity)) as provider:
                response = await client.post('/api/auth/google/exchange', json={**proof, 'session_id': code})
                assert response.status_code == 200
                if verified is None:
                    assert response.json()['status'] == 'link_required' and response.json()['session'] is None
                    assert 'set-cookie' not in response.headers
                    assert await db.oauth_identities.count_documents({'user_id': uid}) == 0
                    assert (await client.post('/api/auth/google/link', json={**proof, 'password': 'Wrong-fixture-password'})).status_code == 400
                    response = await client.post('/api/auth/google/link', json={**proof, 'password': password})
                    assert response.status_code == 200
                assert response.json()['session']['user']['id'] == uid
                assert response.json()['session']['user']['workspace_role'] == 'member'
                assert provider.await_count == 1
            stored = await db.users.find_one({'id': uid})
            assert stored['name'] == 'Existing fixture' and stored['xp'] == 125 and stored['workspace_id'] == wid
            assert stored['password'] == hashed and verify_password(password, stored['password'])
            assert await db.simulations.count_documents({'id': sid, 'user_id': uid}) == 1
            assert (await db.memberships.find_one({'user_id': uid, 'workspace_id': wid}))['role'] == 'member'
            assert await db.users.count_documents({'email': email}) == 1
            # Subsequent Google sign-in uses the bound identity without another password prompt.
            again = (await client.post('/api/auth/google/start')).json(); flows.append(digest(again['state']))
            again_code = prefix + '-again'; codes.append(digest(again_code))
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock(return_value=identity.model_copy(update={'email_verified': None}))):
                result = await client.post('/api/auth/google/exchange', json={
                    'state': again['state'], 'verifier': again['verifier'], 'session_id': again_code})
                assert result.json()['status'] == 'authenticated'
        finally:
            await db.simulations.delete_one({'id': sid})
            await cleanup([uid], flows, codes)


async def test_google_state_expiry_and_provider_failures_do_not_create_accounts():
    prefix = 'google-failure-' + uuid.uuid4().hex
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(prefix, 12345)),
        base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        flow = (await client.post('/api/auth/google/start')).json()
        proof = {k: flow[k] for k in ('state', 'verifier')}; code = prefix + '-opaque'
        try:
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock(side_effect=HTTPException(502, 'Google sign-in is temporarily unavailable.'))):
                result = await client.post('/api/auth/google/exchange', json={**proof, 'session_id': code})
                assert result.status_code == 502 and 'set-cookie' not in result.headers
            await db.oauth_flows.update_one({'_id': digest(flow['state'])}, {'$set': {'expires_at': datetime.now(timezone.utc) - timedelta(seconds=1)}})
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock()) as provider:
                expired = await client.post('/api/auth/google/exchange', json={**proof, 'session_id': code})
                assert expired.status_code == 400 and provider.await_count == 0
            injected = await client.post('/api/auth/google/exchange', json={**proof, 'session_id': code, 'email_verified': True, 'role': 'admin'})
            assert injected.status_code == 422
        finally:
            await cleanup([], [digest(flow['state'])], [digest(code)])


@pytest.mark.parametrize('has_password', [True, False])
async def test_no_known_password_recovery_requires_explicit_approval(has_password):
    from scripts.approve_google_link import approve
    prefix = 'google-recovery-' + uuid.uuid4().hex
    uid = prefix + '-user'
    user = {'id': uid, 'email': prefix + '@example.com', 'name': 'Internal recovery fixture',
        'is_internal': True, 'workspace_id': prefix + '-workspace', 'xp': 210}
    if has_password:
        user['password'] = hash_password('Fixture-Link-Only-2026!')
    await db.users.insert_one(dict(user))
    await db.memberships.insert_one({'workspace_id': user['workspace_id'], 'user_id': uid, 'role': 'member', 'verified': True})
    await db.simulations.insert_one({'id': prefix + '-practice', 'user_id': uid, 'transcript': [{'speaker': 'rep', 'text': 'Fictional saved practice'}]})
    identity = ManagedGoogleIdentity(id=prefix, email=user['email'], name='Google profile name', email_verified=None)
    flow, code = None, prefix + '-opaque'
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, client=(prefix, 12345)),
        base_url='https://test.local', headers={'Origin': 'https://test.local'}) as client:
        try:
            flow = (await client.post('/api/auth/google/start')).json()
            proof = {k: flow[k] for k in ('state', 'verifier')}
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock(return_value=identity)):
                result = await client.post('/api/auth/google/exchange', json={**proof, 'session_id': code})
            assert result.json()['status'] == 'link_required'
            assert result.json()['password_available'] is has_password
            requested = await client.post('/api/auth/google/recovery', json=proof)
            assert requested.status_code == 200
            ref = requested.json()['reference']
            assert ref.startswith('RF-') and requested.json()['status'] == 'pending'
            assert 'set-cookie' not in requested.headers
            assert await db.oauth_identities.count_documents({'user_id': uid}) == 0
            assert (await client.post('/api/auth/google/recovery', json=proof)).json()['reference'] == ref
            assert (await client.post('/api/auth/google/recovery', json={**proof, 'verifier': 'x'*43})).status_code == 400
            assert (await client.post('/api/auth/google/recovery/approve', json={'reference': ref})).status_code == 404
            # Controlled operator approval in this test is explicit, not a public API bypass.
            await approve(ref)
            with patch('routers.google_auth.exchange_managed_identity', AsyncMock()) as provider:
                finished = await client.post('/api/auth/google/exchange', json={**proof, 'session_id': code})
                assert finished.status_code == 200 and finished.json()['status'] == 'authenticated'
                assert finished.json()['session']['user']['id'] == uid
                assert finished.json()['session']['user']['workspace_role'] == 'member'
                assert provider.await_count == 0
            current = await db.users.find_one({'id': uid})
            assert current.get('password') == user.get('password') and current['xp'] == 210
            assert current['name'] == user['name'] and current['workspace_id'] == user['workspace_id']
        finally:
            await db.oauth_recoveries.delete_many({'user_id': uid})
            await db.simulations.delete_many({'user_id': uid})
            await cleanup([uid], [digest(flow['state'])] if flow else [], [digest(code)])


@pytest.mark.parametrize('body,status,expected', [
    ({'id': 'fixture', 'email': 'fixture@example.com', 'name': 'Fixture', 'email_verified': False}, 200, 403),
    ({'id': 'fixture', 'email': 'fixture@example.com', 'name': 'Fixture', 'email_verified': 'true'}, 200, 502),
    ({'email': 'fixture@example.com'}, 200, 502),
    ({'detail': 'provider-private-error-body'}, 500, 502),
])
async def test_upstream_identity_validation_and_sanitization(body, status, expected):
    result = httpx.Response(status, json=body)
    mocked = AsyncMock(); mocked.__aenter__.return_value.get.return_value = result
    with patch('lib.google_auth.httpx.AsyncClient', return_value=mocked):
        with pytest.raises(HTTPException) as failure:
            await exchange_managed_identity('not-a-real-session-id')
        assert failure.value.status_code == expected
        assert 'provider-private-error-body' not in failure.value.detail


async def cleanup(ids, flows, codes):
    await db.oauth_identities.delete_many({'user_id': {'$in': ids}})
    await db.memberships.delete_many({'user_id': {'$in': ids}})
    await db.workspaces.delete_many({'owner_id': {'$in': ids}})
    await db.users.delete_many({'id': {'$in': ids}})
    await db.oauth_flows.delete_many({'_id': {'$in': flows}})
    await db.oauth_codes.delete_many({'_id': {'$in': codes}})